from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from django.core.cache import cache
from data.config import URL_BASE_DATA
from server.config import URL_BASE_SERVER
from server.sort import sort_by_centrality, suggestion
from server.centrality import Centrality
import time
from concurrent.futures import ThreadPoolExecutor

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=2)

class BooksList(APIView):
    def get(self, request, format=None):
        # Generate cache key based on request parameters
        start_time = time.time() 
        
        cache_key = f"books_list_{request.get_full_path()}"
        cached_results = cache.get(cache_key)
        
        if cached_results:
            execution_time = time.time() - start_time
            print(f"BookList returned cached results in {execution_time:.4f} seconds")
            return Response(cached_results)
        
        # Create URL for data API
        url = request.build_absolute_uri()
        url = url.replace(URL_BASE_SERVER, URL_BASE_DATA)
        
        # Make request to data API with shorter timeout
        start_time_request = time.time()
        try:
            response = requests.get(url, timeout=2)
            
            if response.status_code != 200:
                return Response({"error": "Failed to fetch data"}, status=response.status_code)
                
            results = response.json()
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Request failed: {str(e)}"}, status=500)
        
        end_time_request = time.time()
        print(f"BookList data API request time: {end_time_request - start_time_request:.4f} seconds")
        
        # Apply centrality-based sorting only if necessary
        start_time_sort = time.time()
        sort = request.GET.get('sort')
        
        if sort in ['closeness', 'betweenness']:
            ordre = request.GET.get('order', 'descending')
            
            # Process centrality calculation based on dataset size
            if results:
                if len(results) <= 50:  
                    # Generate cache key using first 5 books
                    centrality_cache_key = f"centrality_{sort}_{ordre}_{'_'.join(str(b['id']) for b in results[:5])}"
                    sorted_results = cache.get(centrality_cache_key)
                    
                    if sorted_results:
                        results = sorted_results
                    elif len(results) <= 20:
                        # For small datasets, calculate immediately
                        sorted_results = sort_by_centrality(
                            results, 
                            Centrality.CLOSENESS if sort == 'closeness' else Centrality.BETWEENNESS, 
                            ordre
                        )
                        results = sorted_results
                        # Cache for longer (24 hours)
                        cache.set(centrality_cache_key, sorted_results, timeout=86400)
                    else:
                        # For medium datasets (21-50), calculate in background and use unsorted for now
                        # Submit task to background executor
                        executor.submit(
                            self._background_centrality_calculation,
                            results[:],  # Copy to avoid reference issues
                            Centrality.CLOSENESS if sort == 'closeness' else Centrality.BETWEENNESS,
                            ordre,
                            centrality_cache_key
                        )
        
        end_time_sort = time.time()
        print(f"BookList sorting time: {end_time_sort - start_time_sort:.4f} seconds")
        
        # Get suggestions with optimized approach
        start_time_suggestions = time.time()
        suggestions = []
        
        if results:
            book_ids = [b['id'] for b in results]
            # Only use the first 2 books for suggestions (as in original)
            suggestion_ids = book_ids[:2]
            
            # Check for cached suggestions
            suggestions_cache_key = f"suggestions_{'_'.join(str(id) for id in suggestion_ids)}"
            suggestions = cache.get(suggestions_cache_key)
            
            if not suggestions:
                # Use thread pool to limit suggestion generation time
                try:
                    with ThreadPoolExecutor(max_workers=1) as suggestion_executor:
                        future = suggestion_executor.submit(suggestion, book_ids)
                        # Wait max 2 seconds for suggestions
                        suggestions = future.result(timeout=2.0)
                    # Cache suggestions for longer (24 hours)
                    cache.set(suggestions_cache_key, suggestions, timeout=86400)
                except Exception as e:
                    print(f"Suggestion generation timed out or failed: {e}")
                    suggestions = []  # Empty list if timeout or error
        
        end_time_suggestions = time.time()  
        print(f"BookList suggestions time: {end_time_suggestions - start_time_suggestions:.4f} seconds")
        
        # Prepare response
        response_data = {
            "result": results,
            "suggestions": suggestions
        }
        
        # Cache the entire response for longer (4 hours instead of 1)
        cache.set(cache_key, response_data, timeout=14400)
        
        execution_time = time.time() - start_time
        print(f"BookList query execution time: {execution_time:.4f} seconds")
        return Response(response_data)
    
    @staticmethod
    def _background_centrality_calculation(results, centrality_type, ordre, cache_key):
        """Background task for centrality calculation"""
        try:
            print(f"Starting background centrality calculation for {cache_key}")
            start_time = time.time()
            
            # Calculate centrality
            sorted_results = sort_by_centrality(results, centrality_type, ordre)
            
            # Cache the results for 24 hours
            cache.set(cache_key, sorted_results, timeout=86400)
            
            print(f"Background centrality calculation completed in {time.time() - start_time:.4f} seconds")
        except Exception as e:
            print(f"Background centrality calculation failed: {e}")