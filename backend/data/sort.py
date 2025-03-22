import time
from django.core.cache import cache

from data.graph import UnweightedGraph, WeightedGraph
from data.centrality import *
from data.config import URL_BASE_DATA
from backend.config import URL_NEIGHBOR, URL_BASE, construct_url_requete_search
from data.models import Book, Neighbors
from data.serializers import BookSerializer

NUMBER_SUGGESTION = 10
SUGGESTION_TIMEOUT = 86400  # 24 hours cache for suggestions
CENTRALITY_TIMEOUT = 86400  # 24 hours cache for centrality calculations

def suggestion(book_ids):
    """Get book suggestions with direct database access instead of HTTP requests"""
    # Generate cache key for entire suggestion list
    start_time = time.time()
    
    # Only use first 2 books for suggestions cache key
    suggestions_cache_key = f"suggestions_{'_'.join(str(id) for id in book_ids[:2])}"
    cached_suggestions = cache.get(suggestions_cache_key)
    
    if cached_suggestions:
        print(f"Using cached suggestions for {book_ids[:2]}")
        return cached_suggestions
        
    book_suggestion = []
    book_suggestion_id = set()
    number_book_in_suggestion = 0
    
    # Process only the first 2 books (as in original)
    for book_id in book_ids[:2]:
        # Check timeout - stop if taking too long
        if time.time() - start_time > 2.0:  # 2 second timeout
            print(f"Suggestion generation timed out after {time.time() - start_time:.2f}s")
            break
            
        # Check for single book suggestion cache
        single_book_cache_key = f"suggestion_single_{book_id}"
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
            # Direct database access instead of HTTP request
            try:
                # Get the book
                book = Book.objects.get(pk=book_id)
                
                # Get neighbors from database
                try:
                    book_neighbors = Neighbors.objects.get(book=book)
                    neighbor_books = book_neighbors.neighbors.all()
                    
                    # Serialize the neighbors
                    single_book_results = BookSerializer(neighbor_books, many=True).data
                    
                    # Cache these single book results
                    cache.set(single_book_cache_key, single_book_results, timeout=SUGGESTION_TIMEOUT)
                    
                    for book_data in single_book_results:
                        if book_data['id'] not in book_suggestion_id and book_data['id'] not in book_ids:
                            number_book_in_suggestion += 1
                            book_suggestion.append(book_data)
                            book_suggestion_id.add(book_data['id'])
                            if number_book_in_suggestion >= NUMBER_SUGGESTION:
                                # Cache final result before returning
                                cache.set(suggestions_cache_key, book_suggestion, timeout=SUGGESTION_TIMEOUT)
                                return book_suggestion
                except Neighbors.DoesNotExist:
                    # No neighbors found, continue with next book
                    continue
            except Book.DoesNotExist:
                # Skip this book if it doesn't exist
                continue
    
    # Cache final result before returning
    cache.set(suggestions_cache_key, book_suggestion, timeout=SUGGESTION_TIMEOUT)
    print(f"Generated {len(book_suggestion)} suggestions in {time.time() - start_time:.4f} seconds")
    return book_suggestion

def intersection(lst1, lst2):
    """Compute intersection of two lists efficiently"""
    # Use sets for faster intersection
    if not lst1 or not lst2:
        return []
    return list(set(lst1) & set(lst2))

def sort_by_centrality(search, centrality, ordre):
    """Sort search results by centrality with optimized performance"""
    # Early return for empty or single-item search results
    if not search or len(search) <= 1:
        return search
        
    # Check cache first
    cache_key = f"centrality_{centrality.name}_{ordre}_{'_'.join(str(b['id']) for b in search[:5])}"
    cached_result = cache.get(cache_key)
    if cached_result:
        print(f"Using cached centrality results for {centrality.name}")
        return cached_result
    
    # Set start time for timeout tracking
    start_time = time.time()
    
    # Create appropriate graph
    G = UnweightedGraph() if centrality == Centrality.BETWEENNESS else WeightedGraph()
    
    # Add nodes to graph
    for book in search:
        G.add_node(book)
    
    # Determine algorithm parameters based on dataset size
    num_books = len(search)
    # For larger datasets, limit complexity
    timeout_threshold = 0.75 if num_books > 50 else (1.0 if num_books > 30 else 2.0)
    max_edges = 500 if num_books > 50 else (750 if num_books > 30 else 1000)
    
    print(f"Centrality calculation for {num_books} books, timeout: {timeout_threshold}s, max edges: {max_edges}")
    
    # Precompute subject intersections for all pairs to avoid repeated calculations
    subject_intersections = {}
    for i, node1 in enumerate(G.nodes):
        # Check timeout
        if time.time() - start_time > timeout_threshold:
            print(f"Timeout during subject intersection calculation: {time.time() - start_time:.2f}s")
            break
            
        node1_subjects = set(node1.json.get("subjects", []))
        
        for j, node2 in enumerate(G.nodes[i+1:], i+1):
            # Get subjects once
            node2_subjects = set(node2.json.get("subjects", []))
            
            # Compute intersection
            weight = len(node1_subjects & node2_subjects)
            
            if weight > 0:
                # Store with a tuple key ordered by node IDs for consistent lookup
                key = (node1.json['id'], node2.json['id'])
                subject_intersections[key] = weight
    
    # Build edges using precomputed intersections
    edge_count = 0
    for i, n in enumerate(G.nodes):
        # Check timeout
        if time.time() - start_time > timeout_threshold:
            print(f"Timeout during edge building: {time.time() - start_time:.2f}s")
            break
            
        for j, m in enumerate(G.nodes[i+1:], i+1):
            # Skip if already neighbors
            if m in n.neighbors:
                continue
                
            # For large datasets, don't create all possible edges
            if edge_count >= max_edges:
                break
                
            # Lookup intersection weight from precomputed values
            key = (n.json['id'], m.json['id'])
            alt_key = (m.json['id'], n.json['id'])
            weight = subject_intersections.get(key, subject_intersections.get(alt_key, 0))
            
            if weight > 0:
                edge_count += 1
                if centrality == Centrality.BETWEENNESS:
                    G.add_edge(n, m)
                else:
                    G.add_edge(n, m, weight)
    
    print(f"Created {edge_count} edges in {time.time() - start_time:.4f} seconds")
    
    # Compute centrality - with simplified calculation for larger graphs
    centrality_start = time.time()
    if centrality == Centrality.BETWEENNESS:
        if num_books <= 30:
            compute_betweenness_centrality(G)
        else:
            # For larger graphs, use simplified betweenness calculation
            compute_betweenness_centrality_simplified(G)
    else:
        compute_closeness_centrality(G)
    
    print(f"Centrality computation took {time.time() - centrality_start:.4f} seconds")
    
    # Sort nodes by centrality measure
    G.sort_nodes_by_centrality_measure(ordre)
    
    # Get sorted results
    sorted_results = [n.json for n in G.nodes]
    
    # Cache results before returning
    cache.set(cache_key, sorted_results, timeout=CENTRALITY_TIMEOUT)
    
    total_time = time.time() - start_time
    print(f"Total centrality calculation completed in {total_time:.4f} seconds")
    return sorted_results

def compute_betweenness_centrality_simplified(G):
    """Simplified betweenness centrality for larger graphs - samples nodes"""
    # Get top 20 most connected nodes as representative sample
    sample_nodes = sorted(G.nodes, key=lambda n: len(n.neighbors), reverse=True)[:20]
    
    # Initialize centrality scores
    for node in G.nodes:
        node.centrality_measure = 0
    
    # Only compute for sample nodes (approximation)
    for node in sample_nodes:
        # Compute approximate betweenness using local neighborhood structure
        # First-level neighbors get a weight of 1
        local_paths = 0
        neighbors_set = set(node.neighbors)
        
        for n1 in neighbors_set:
            # Second-level neighbors through this node get a weight of 0.5
            for n2 in n1.neighbors:
                if n2 not in neighbors_set and n2 != node:
                    local_paths += 0.5
        
        # Assign measure based on local network centrality
        node.centrality_measure = len(node.neighbors) + local_paths