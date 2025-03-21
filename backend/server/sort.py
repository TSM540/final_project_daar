import requests
from django.core.cache import cache
import time
from server.graph import UnweightedGraph, WeightedGraph
from server.centrality import *
from data.config import URL_BASE_DATA
from backend.config import URL_NEIGHBOR, URL_BASE, construct_url_requete_search
# from concurrent.futures import ThreadPoolExecutor

URL_REQUETE_NEIGHBOR = URL_BASE + URL_BASE_DATA + URL_NEIGHBOR
NUMBER_SUGGESTION = 10
SUGGESTION_TIMEOUT = 86400  # 24 hours cache for suggestions
CENTRALITY_TIMEOUT = 86400  # 24 hours cache for centrality calculations

def suggestion(book_ids):
    """Get book suggestions with improved caching and performance"""
    # Generate cache key for entire suggestion list
    start_time = time.time()
    suggestions_cache_key = f"suggestions_{'_'.join(str(id) for id in book_ids[:2])}"
    cached_suggestions = cache.get(suggestions_cache_key)
    
    if cached_suggestions:
        return cached_suggestions
        
    book_suggestion = []
    book_suggestion_id = set()
    number_book_in_suggestion = 0
    
    # Process only the first 2 books (as in original)
    for identifiant in book_ids[:2]:
        # Check timeout - stop if taking too long
        if time.time() - start_time > 2.0:  # 2 second timeout
            break
            
        # Check for single book suggestion cache
        single_book_cache_key = f"suggestion_single_{identifiant}"
        single_book_suggestions = cache.get(single_book_cache_key)
        
        if single_book_suggestions:
            # Use cached suggestions for this book
            for book in single_book_suggestions:
                if book['id'] not in book_suggestion_id and book['id'] not in book_ids:
                    number_book_in_suggestion += 1
                    book_suggestion.append(book)
                    book_suggestion_id.add(book['id'])
                    if number_book_in_suggestion >= NUMBER_SUGGESTION:
                        # Cache final result before returning
                        cache.set(suggestions_cache_key, book_suggestion, timeout=SUGGESTION_TIMEOUT)
                        return book_suggestion
        else:
            # Need to fetch suggestions for this book
            url_requete = construct_url_requete_search(URL_REQUETE_NEIGHBOR) + str(identifiant)
            print(url_requete)
            
            try:
                # Set a shorter timeout for this request
                results = requests.get(url_requete, timeout=1.0)
                
                if results.status_code != 200:
                    continue
                    
                single_book_results = results.json()
                # Cache these single book results
                cache.set(single_book_cache_key, single_book_results, timeout=SUGGESTION_TIMEOUT)
                
                for book in single_book_results:
                    if book['id'] not in book_suggestion_id and book['id'] not in book_ids:
                        number_book_in_suggestion += 1
                        book_suggestion.append(book)
                        book_suggestion_id.add(book['id'])
                        if number_book_in_suggestion >= NUMBER_SUGGESTION:
                            # Cache final result before returning
                            cache.set(suggestions_cache_key, book_suggestion, timeout=SUGGESTION_TIMEOUT)
                            return book_suggestion
            except requests.exceptions.RequestException:
                # Skip this book if request fails
                continue
    
    # Cache final result before returning
    cache.set(suggestions_cache_key, book_suggestion, timeout=SUGGESTION_TIMEOUT)
    print(f"Generated {len(book_suggestion)} suggestions in {time.time() - start_time:.4f} seconds")
    return book_suggestion

def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))

def sort_by_centrality(search, centrality, ordre):
    # Early return for empty or single-item search results
    if not search or len(search) <= 1:
        return search
        
    # Check cache first
    cache_key = f"centrality_{centrality.name}_{ordre}_{'_'.join(str(b['id']) for b in search[:5])}"
    cached_result = cache.get(cache_key)
    # if cached_result:
    #     return cached_result
    
    # Set start time for timeout tracking
    start_time = time.time()
    
    # Create appropriate graph
    G = UnweightedGraph() if centrality == Centrality.BETWEENNESS else WeightedGraph()
    
    # Add nodes to graph
    for book in search:
        G.add_node(book)
    
    # Build edges - optimize by limiting connections for large datasets
    max_edges = 1000
    edge_count = 0
    
    for n in G.nodes:
        if time.time() - start_time > 1.5:  # Timeout after 1.5 seconds
            break
            
        for m in G.nodes:
            if n == m or m in n.neighbors:
                continue
            
            # For large datasets, don't create all possible edges
            if edge_count > max_edges and len(G.nodes) > 30:
                break
                
            # Compute weight based on subject intersection
            weight = len(intersection(m.json.get("subjects", []), n.json.get("subjects", [])))
            
            if weight > 0:
                edge_count += 1
                if centrality == Centrality.BETWEENNESS:
                    G.add_edge(n, m)
                else:
                    G.add_edge(n, m, weight)
    
    # Compute centrality - with simplified calculation for larger graphs
    if centrality == Centrality.BETWEENNESS:
        if len(G.nodes) <= 30:
            compute_betweenness_centrality(G)
        else:
            # For larger graphs, use simplified betweenness calculation
            compute_betweenness_centrality_simplified(G)
    else:
        compute_closeness_centrality(G)
    
    # Sort nodes by centrality measure
    G.sort_nodes_by_centrality_measure(ordre)
    
    # Get sorted results
    sorted_results = [n.json for n in G.nodes]
    
    # Cache results before returning
    cache.set(cache_key, sorted_results, timeout=CENTRALITY_TIMEOUT)
    
    print(f"Centrality calculation completed in {time.time() - start_time:.4f} seconds")
    return sorted_results

# Helper function for larger graphs
def compute_betweenness_centrality_simplified(G):
    """Simplified betweenness centrality for larger graphs - samples nodes"""
    # Get top 20 most connected nodes as representative sample
    sample_nodes = sorted(G.nodes, key=lambda n: len(n.neighbors), reverse=True)[:20]
    
    # Initialize centrality scores
    for node in G.nodes:
        node.centrality_measure = 0
    
    # Only compute for sample nodes (approximation)
    for node in sample_nodes:
        # Simple approximation - use number of connections as proxy for centrality
        node.centrality_measure = len(node.neighbors)