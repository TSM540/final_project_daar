import requests
from server.graph import UnweightedGraph, WeightedGraph
from server.centrality import Centrality, compute_betweenness_centrality, compute_closeness_centrality
from data.config import URL_BASE_DATA
from backend.config import URL_NEIGHBOR, URL_BASE, construct_url_requete_search
from django.core.cache import cache

URL_REQUETE_NEIGHBOR = URL_BASE + URL_BASE_DATA + URL_NEIGHBOR
NUMBER_SUGGESTION = 10

def suggestion(book_ids):
    """
    Get book suggestions based on neighbors of the first few books
    """
    book_suggestions = []
    book_suggestion_id = set()
    number_book_in_suggestion = 0
    
    # Only process the first 2 books for suggestions to minimize API calls
    for identifiant in book_ids[:2]:
        # Check cache first
        cache_key = f"book_neighbors_{identifiant}"
        cached_neighbors = cache.get(cache_key)
        
        if cached_neighbors:
            neighbors_data = cached_neighbors
        else:
            # Make API request with timeout
            url_requete = construct_url_requete_search(URL_REQUETE_NEIGHBOR) + str(identifiant)
            try:
                response = requests.get(url_requete, timeout=3)
                if response.status_code != 200:
                    continue
                
                neighbors_data = response.json()
                # Cache the neighbors data
                cache.set(cache_key, neighbors_data, timeout=3600)
            except requests.exceptions.RequestException:
                continue
        
        # Process neighbors data
        for book in neighbors_data:
            if book['id'] not in book_suggestion_id and book['id'] not in book_ids:
                number_book_in_suggestion += 1
                book_suggestions.append(book)
                book_suggestion_id.add(book['id'])
                
                if number_book_in_suggestion >= NUMBER_SUGGESTION:
                    return book_suggestions
    
    return book_suggestions

def intersection(lst1, lst2):
    """
    Compute the intersection of two lists efficiently
    """
    if not lst1 or not lst2:
        return []
    
    # Use set intersection for efficiency
    return list(set(lst1) & set(lst2))

def sort_by_centrality(search, centrality_type, ordre):
    """
    Sort books by centrality measure with optimizations
    """
    # Return early if search is empty or has only one item
    if not search or len(search) < 2:
        return search
    
    # Create appropriate graph type
    G = UnweightedGraph() if centrality_type == Centrality.BETWEENNESS else WeightedGraph()
    
    # Add nodes to graph
    for book in search:
        G.add_node(book)
    
    # Cache mapping of subjects to books to avoid repeated lookups
    subject_to_books = {}
    for book in search:
        for subject in book.get("subjects", []):
            if subject not in subject_to_books:
                subject_to_books[subject] = []
            subject_to_books[subject].append(book)
    
    # Add edges with optimized subject intersection
    for i, n in enumerate(G.nodes):
        # Get subjects once
        n_subjects = n.json.get("subjects", [])
        if not n_subjects:
            continue
            
        for subject in n_subjects:
            # Use cached subject mapping
            for book in subject_to_books.get(subject, []):
                m = G.add_node(book)
                if m and n != m and m not in n.neighbors:
                    # Add edge based on centrality type
                    if centrality_type == Centrality.BETWEENNESS:
                        G.add_edge(n, m)
                    else:
                        # Calculate weight based on subject intersection
                        weight = len(intersection(n_subjects, book.get("subjects", [])))
                        if weight > 0:
                            G.add_edge(n, m, weight)
    
    # Apply appropriate centrality calculation
    if centrality_type == Centrality.BETWEENNESS:
        compute_betweenness_centrality(G)
    else:
        compute_closeness_centrality(G)
    
    # Sort nodes by centrality measure
    G.sort_nodes_by_centrality_measure(ordre)
    
    # Return sorted results
    return [n.json for n in G.nodes]