from django.core.management.base import BaseCommand
import networkx as nx
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from ...models import Book, Neighbors
from django.db.models import Count, Q
from tqdm import tqdm
import sys
import random
import matplotlib.cm as cm

# Import des classes de graph.py
from ...graph import NodeWeighted, WeightedGraph, UnweightedGraph, NodeUnweighted

class Command(BaseCommand):
    help = 'Visualiser en 3D le graphe des relations entre livres basé sur Neighbors et graph.py'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, default='graph_3d_visualization.png',
                            help='Chemin du fichier pour sauvegarder la visualisation')
        parser.add_argument('--weighted', action='store_true',
                            help='Utiliser un graphe pondéré (sinon, non pondéré par défaut)')
        parser.add_argument('--sample', type=int, default=0,
                            help='Limiter à un échantillon de N livres (0 = tous)')
        parser.add_argument('--min_neighbors', type=int, default=1,
                            help='Nombre minimum de voisins pour inclure un livre')
        parser.add_argument('--jaccard', action='store_true',
                            help='Calculer la similarité de Jaccard comme poids (pour graphe pondéré)')
        parser.add_argument('--max_edges', type=int, default=100000,
                            help='Nombre maximum d\'arêtes à afficher (pour les performances)')
        parser.add_argument('--edge_visibility', type=float, default=0.3,
                            help='Visibilité des arêtes (alpha) entre 0.1 et 1.0')
        parser.add_argument('--edge_color_by_weight', action='store_true',
                            help='Colorer les arêtes selon leur poids (pour graphe pondéré)')
        parser.add_argument('--highlight_communities', action='store_true',
                            help='Mettre en évidence les communautés de livres')

    def handle(self, *args, **options):
        output_file = options['output']
        weighted = options['weighted']
        sample_size = options['sample']
        min_neighbors = options['min_neighbors']
        use_jaccard = options['jaccard']
        max_edges = options['max_edges']
        edge_visibility = max(0.1, min(1.0, options['edge_visibility']))
        edge_color_by_weight = options['edge_color_by_weight']
        highlight_communities = options['highlight_communities']
        
        self.stdout.write(self.style.SUCCESS("Chargement des données..."))
        
        # Filtrer les livres qui ont au moins min_neighbors voisins
        neighbors_with_count = Neighbors.objects.annotate(
            count=Count('neighbors')
        ).filter(count__gte=min_neighbors)
        
        if sample_size > 0:
            neighbors_with_count = neighbors_with_count[:sample_size]
            
        total_count = neighbors_with_count.count()
        
        if total_count == 0:
            self.stdout.write(self.style.ERROR(f"Aucun livre avec au moins {min_neighbors} voisins trouvé!"))
            return
            
        self.stdout.write(self.style.SUCCESS(f"Construction du graphe pour {total_count} livres..."))
        
        # Créer le graphe approprié selon l'option
        if weighted:
            graph = WeightedGraph()
            self.stdout.write(self.style.SUCCESS("Utilisation d'un graphe pondéré"))
        else:
            graph = UnweightedGraph()
            self.stdout.write(self.style.SUCCESS("Utilisation d'un graphe non pondéré"))
        
        # Dictionnaire pour stocker les objets Node créés par book_id
        nodes_dict = {}
        
        # Barre de progression
        progress = tqdm(total=total_count, file=sys.stdout)
        
        # Pour chaque objet Neighbors, créer un nœud et ses relations
        for neighbor_obj in neighbors_with_count:
            book = neighbor_obj.book
            book_id = book.gutenberg_id
            book_info = {
                'id': book_id,
                'title': book.title,
                'download_count': book.download_count,
                'languages': [lang.code for lang in book.languages.all()]
            }
            
            # Créer ou récupérer le nœud pour ce livre
            if book_id not in nodes_dict:
                if weighted:
                    node = NodeWeighted(book_info)
                else:
                    node = NodeUnweighted(book_info)
                nodes_dict[book_id] = node
                graph.nodes.append(node)
            else:
                node = nodes_dict[book_id]
            
            # Ajouter les relations avec tous les voisins
            for neighbor_book in neighbor_obj.neighbors.all():
                neighbor_id = neighbor_book.gutenberg_id
                neighbor_info = {
                    'id': neighbor_id,
                    'title': neighbor_book.title,
                    'download_count': neighbor_book.download_count,
                    'languages': [lang.code for lang in neighbor_book.languages.all()]
                }
                
                # Créer ou récupérer le nœud pour le voisin
                if neighbor_id not in nodes_dict:
                    if weighted:
                        neighbor_node = NodeWeighted(neighbor_info)
                    else:
                        neighbor_node = NodeUnweighted(neighbor_info)
                    nodes_dict[neighbor_id] = neighbor_node
                    graph.nodes.append(neighbor_node)
                else:
                    neighbor_node = nodes_dict[neighbor_id]
                
                # Ajouter l'arête entre le livre et son voisin
                if weighted:
                    # Calculer un poids pour l'arête
                    if use_jaccard:
                        # Calculer la similarité de Jaccard entre les sujets des deux livres
                        book_subjects = set(book.subjects.values_list('id', flat=True))
                        neighbor_subjects = set(neighbor_book.subjects.values_list('id', flat=True))
                        
                        if book_subjects or neighbor_subjects:
                            jaccard = len(book_subjects.intersection(neighbor_subjects)) / len(book_subjects.union(neighbor_subjects)) if book_subjects.union(neighbor_subjects) else 0
                        else:
                            jaccard = 0
                        
                        weight = jaccard
                    else:
                        # Utiliser un poids de 1.0 par défaut
                        weight = 1.0
                    
                    node.add_neighbor(neighbor_node, weight)
                    neighbor_node.add_neighbor(node, weight)
                else:
                    node.add_neighbor(neighbor_node)
                    neighbor_node.add_neighbor(node)
            
            progress.update(1)
        
        progress.close()
        
        self.stdout.write(self.style.SUCCESS(f"Graphe construit avec {len(graph.nodes)} nœuds"))
        
        # Convertir notre graphe en graphe NetworkX pour la visualisation
        nx_graph = nx.Graph()
        
        # Ajouter les nœuds avec leurs attributs
        for node in graph.nodes:
            nx_graph.add_node(node.json['id'], **node.json)
        
        # Ajouter les arêtes
        if weighted:
            for node in graph.nodes:
                for neighbor, weight in node.neighbors.items():
                    nx_graph.add_edge(node.json['id'], neighbor.json['id'], weight=weight)
        else:
            for node in graph.nodes:
                for neighbor in node.neighbors:
                    nx_graph.add_edge(node.json['id'], neighbor.json['id'])
        
        self.stdout.write(self.style.SUCCESS(f"Graphe NetworkX créé avec {nx_graph.number_of_nodes()} nœuds et {nx_graph.number_of_edges()} arêtes"))

        # Détection des communautés si demandé
        node_colors = []
        if highlight_communities and nx_graph.number_of_nodes() > 0:
            self.stdout.write(self.style.SUCCESS("Détection des communautés..."))
            try:
                communities = nx.community.greedy_modularity_communities(nx_graph)
                self.stdout.write(self.style.SUCCESS(f"Détection de {len(communities)} communautés"))
                
                # Créer un dictionnaire pour mapper chaque nœud à sa communauté
                community_map = {}
                for i, community in enumerate(communities):
                    for node in community:
                        community_map[node] = i
                
                # Couleur des nœuds basée sur leur communauté
                node_colors = [community_map.get(node, 0) for node in nx_graph.nodes()]
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Erreur lors de la détection des communautés: {e}"))
                # Utiliser le degré comme couleur par défaut
                node_colors = [nx_graph.degree[node] for node in nx_graph.nodes()]
        else:
            # Calculer le degré des nœuds pour la couleur
            node_colors = [nx_graph.degree[node] for node in nx_graph.nodes()]
        
        # Générer un layout 3D
        self.stdout.write(self.style.SUCCESS("Génération du layout 3D..."))
        pos_3d = nx.spring_layout(nx_graph, dim=3, seed=42, iterations=50, weight='weight' if weighted else None)
        
        # Préparer la visualisation 3D
        fig = plt.figure(figsize=(14, 12))
        ax = fig.add_subplot(111, projection='3d')
        
        # Extraire les coordonnées x, y, z
        xs = [pos_3d[node][0] for node in nx_graph.nodes()]
        ys = [pos_3d[node][1] for node in nx_graph.nodes()]
        zs = [pos_3d[node][2] for node in nx_graph.nodes()]
        
        # Taille des nœuds proportionnelle au degré
        node_sizes = [max(20, min(200, nx_graph.degree[node]*3)) for node in nx_graph.nodes()]
        
        # Dessiner les nœuds
        sc = ax.scatter(xs, ys, zs, c=node_colors, cmap='viridis', s=node_sizes, alpha=0.8)
        
        # Ajouter une barre de couleur pour les nœuds
        cbar = fig.colorbar(sc, ax=ax, pad=0.1)
        if highlight_communities:
            cbar.set_label('Communauté')
        else:
            cbar.set_label('Degré du nœud (nombre de voisins)')
        
        # Dessiner les arêtes
        self.stdout.write(self.style.SUCCESS("Dessin des arêtes..."))
        
        # Limiter le nombre d'arêtes à dessiner si nécessaire pour les performances
        edges_to_draw = list(nx_graph.edges())
        if len(edges_to_draw) > max_edges:
            self.stdout.write(self.style.WARNING(f"Trop d'arêtes ({len(edges_to_draw)}), limitation à {max_edges} pour la visualisation"))
            edges_to_draw = random.sample(edges_to_draw, max_edges)
        
        # Obtenir les poids des arêtes pour la colorisation
        if weighted and edge_color_by_weight:
            edge_weights = [nx_graph[u][v].get('weight', 1.0) for u, v in edges_to_draw]
            
            # Normaliser les poids pour la colorisation
            min_weight = min(edge_weights) if edge_weights else 0
            max_weight = max(edge_weights) if edge_weights else 1
            norm_weights = [(w - min_weight) / (max_weight - min_weight) if max_weight != min_weight else 0.5 for w in edge_weights]
            
            # Créer une colormap pour les arêtes
            edge_cmap = plt.cm.get_cmap('plasma')
            edge_colors = [edge_cmap(w) for w in norm_weights]
        else:
            edge_colors = ['gray'] * len(edges_to_draw)
        
        # Dessiner les arêtes avec une meilleure visibilité
        for i, edge in enumerate(tqdm(edges_to_draw, desc="Dessin des arêtes")):
            x1, y1, z1 = pos_3d[edge[0]]
            x2, y2, z2 = pos_3d[edge[1]]
            
            # Obtenir le poids de l'arête si c'est un graphe pondéré
            if weighted and 'weight' in nx_graph[edge[0]][edge[1]]:
                weight = nx_graph[edge[0]][edge[1]]['weight']
                width = max(0.5, min(3.0, weight * 4))  # Largeur proportionnelle au poids
                alpha = max(edge_visibility * 0.5, min(1.0, weight * edge_visibility))  # Alpha proportionnelle au poids
            else:
                width = 0.7
                alpha = edge_visibility
            
            line = np.array([[x1, y1, z1], [x2, y2, z2]])
            ax.plot(line[:, 0], line[:, 1], line[:, 2], linewidth=width, color=edge_colors[i], alpha=alpha)
        
        # Si les arêtes sont colorées par poids, ajouter une seconde barre de couleur
        if weighted and edge_color_by_weight:
            sm = plt.cm.ScalarMappable(cmap='plasma', norm=plt.Normalize(min_weight, max_weight))
            sm.set_array([])
            cbar2 = fig.colorbar(sm, ax=ax, pad=0.15, location='right')
            cbar2.set_label('Poids des arêtes')
        
        # Configurer la visualisation
        title = "Graphe 3D des relations entre livres"
        if weighted:
            title += " (pondéré"
            if use_jaccard:
                title += " par similarité Jaccard)"
            else:
                title += ")"
        ax.set_title(title)
        
        # Éviter les labels sur les axes pour une visualisation plus claire
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_zticklabels([])
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        
        # Annoter quelques nœuds importants (les plus connectés)
        if nx_graph.number_of_nodes() > 0:
            # Sélectionner les 5 nœuds les plus connectés
            top_nodes = sorted(nx_graph.degree, key=lambda x: x[1], reverse=True)[:5]
            for node_id, degree in top_nodes:
                node_pos = pos_3d[node_id]
                node_title = nx_graph.nodes[node_id].get('title', f'ID: {node_id}')
                ax.text(node_pos[0], node_pos[1], node_pos[2], 
                        f"{node_title[:20]}...", 
                        size=8, zorder=1, color='black')
        
        # Enregistrer la visualisation
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        
        self.stdout.write(self.style.SUCCESS(f"Visualisation 3D sauvegardée dans {output_file}"))
        
        # Afficher quelques statistiques sur le graphe
        if nx_graph.number_of_nodes() > 0:
            avg_degree = sum(dict(nx_graph.degree()).values()) / nx_graph.number_of_nodes()
            self.stdout.write(self.style.SUCCESS(f"Degré moyen: {avg_degree:.2f}"))
            
            density = nx.density(nx_graph)
            self.stdout.write(self.style.SUCCESS(f"Densité du graphe: {density:.4f}"))
            
            connected_components = list(nx.connected_components(nx_graph))
            self.stdout.write(self.style.SUCCESS(f"Nombre de composantes connexes: {len(connected_components)}"))
            
            if connected_components:
                largest_component = max(connected_components, key=len)
                self.stdout.write(self.style.SUCCESS(f"Taille de la plus grande composante connexe: {len(largest_component)} nœuds"))
                
            # Calculer et afficher les stats sur les arêtes
            if weighted:
                edge_weights = [nx_graph[u][v].get('weight', 0) for u, v in nx_graph.edges()]
                if edge_weights:
                    self.stdout.write(self.style.SUCCESS(f"Poids moyen des arêtes: {np.mean(edge_weights):.4f}"))
                    self.stdout.write(self.style.SUCCESS(f"Poids min/max des arêtes: {min(edge_weights):.4f}/{max(edge_weights):.4f}"))
                
            # Générer aussi une visualisation simplifiée des principales connexions
            if nx_graph.number_of_edges() > 1000:
                self.stdout.write(self.style.SUCCESS("Génération d'une visualisation simplifiée des connexions principales..."))
                
                # Créer un sous-graphe avec les nœuds les plus connectés
                top_nodes = [node for node, _ in sorted(nx_graph.degree, key=lambda x: x[1], reverse=True)[:50]]
                subgraph = nx_graph.subgraph(top_nodes)
                
                # Générer une visualisation 2D
                fig2, ax2 = plt.subplots(figsize=(12, 10))
                pos_2d = nx.spring_layout(subgraph, seed=42)
                
                # Dessiner les nœuds
                nx.draw_networkx_nodes(subgraph, pos_2d, node_size=100, node_color='blue', alpha=0.8)
                
                # Dessiner les arêtes
                nx.draw_networkx_edges(subgraph, pos_2d, width=0.7, alpha=0.5)
                
                # Ajouter les labels pour les nœuds
                labels = {node: subgraph.nodes[node].get('title', f'ID: {node}')[:15] for node in subgraph.nodes()}
                nx.draw_networkx_labels(subgraph, pos_2d, labels, font_size=8)
                
                plt.title("Graphe des connexions principales entre livres")
                plt.axis('off')
                
                # Enregistrer la visualisation
                simplified_output = output_file.replace('.png', '_simplified.png')
                plt.savefig(simplified_output, dpi=300, bbox_inches='tight')
                self.stdout.write(self.style.SUCCESS(f"Visualisation simplifiée sauvegardée dans {simplified_output}"))