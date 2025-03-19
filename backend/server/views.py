from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from django.core.cache import cache
from data.config import URL_BASE_DATA
from server.config import URL_BASE_SERVER
from server.sort import sort_by_centrality, suggestion
from server.centrality import Centrality

class BooksList(APIView):
    def get(self, request, format=None):
        # Generate cache key based on request parameters
        cache_key = f"books_list_{request.get_full_path()}"
        cached_results = cache.get(cache_key)
        
        if cached_results:
            return Response(cached_results)
        
        # Create URL for data API
        url = request.build_absolute_uri()
        url = url.replace(URL_BASE_SERVER, URL_BASE_DATA)
        
        # Make request to data API with timeout
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code != 200:
                return Response({"error": "Failed to fetch data"}, status=response.status_code)
                
            results = response.json()
            print(results)
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Request failed: {str(e)}"}, status=500)
        
        # Apply centrality-based sorting only if necessary
        sort = request.GET.get('sort')
        if sort in ['closeness', 'betweenness']:
            ordre = request.GET.get('order', 'descending')
            
            # Limit the number of items to process for centrality
            if results and len(results) <= 50:  # Reduced from 100 to 50 for better performance
                centrality_cache_key = f"centrality_{sort}_{ordre}_{'_'.join(str(b['id']) for b in results[:5])}"
                sorted_results = cache.get(centrality_cache_key)
                
                if not sorted_results:
                    sorted_results = sort_by_centrality(results, Centrality.CLOSENESS if sort == 'closeness' else Centrality.BETWEENNESS, ordre)
                    
                    # Cache the centrality calculation results
                    cache.set(centrality_cache_key, sorted_results, timeout=3600)
                
                results = sorted_results
        
        # Get suggestions only if we have results
        suggestions = []
        if results:
            book_ids = [b['id'] for b in results]
            # Only use the first 2 books for suggestions
            suggestion_ids = book_ids[:2]
            
            # Check for cached suggestions
            suggestions_cache_key = f"suggestions_{'_'.join(str(id) for id in suggestion_ids)}"
            suggestions = cache.get(suggestions_cache_key)
            
            if not suggestions:
                suggestions = suggestion(book_ids)
                # Cache suggestions
                cache.set(suggestions_cache_key, suggestions, timeout=3600)
        
        # Prepare response
        response_data = {
            "result": results,
            "suggestions": suggestions
        }
        
        # Cache the entire response
        cache.set(cache_key, response_data, timeout=3600)
        
        return Response(response_data)