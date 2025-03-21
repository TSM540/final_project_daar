from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.http import Http404
from data.models import Book, KeywordsEnglish, KeywordsFrench, KeywordBookEnglish, KeywordBookFrench, Neighbors
from data.serializers import BookSerializer
import numpy as np
from collections import defaultdict
from django.db.models import Q
import time
# Create your views here.


class BookViewSet(APIView):
    
    def get(self, request, format=None):
        start_time = time.time()
        
        # Call the processing function
        queryset = self.process_book_query(request)
        
        # Serialize and return the response
        serializer = BookSerializer(queryset, many=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"BookViewSet query execution time: {execution_time:.4f} seconds")
        
        return Response(serializer.data)
    
    def process_book_query(self, request):
        # Initialize base queryset
        queryset = Book.objects.exclude(download_count__isnull=True)
        queryset = queryset.exclude(title__isnull=True)
        
        # Process language filter
        language = request.GET.get('languages')
        if language is not None:
            queryset = queryset.filter(languages__code=language)
        
        # Process author name filter
        queryset = self._filter_by_author(request, queryset)
        
        # Process title filter
        queryset = self._filter_by_title(request, queryset)
        
        # Process keyword filter
        queryset = self._filter_by_keyword(request, queryset, language)
        
        # Apply sorting
        queryset = self._apply_sorting(request, queryset)
        
        return queryset.distinct()
    
    def _filter_by_author(self, request, queryset):
        search_name_author = request.GET.get('author_name')
        if search_name_author is not None:
            search_name_authors_type = request.GET.get('author_name_type')
            search_name_authors_type = "classique" if search_name_authors_type is None else search_name_authors_type
            
            if search_name_authors_type == "classique":
                queryset = queryset.filter(authors__name__icontains=search_name_author)
            else:
                queryset = queryset.filter(authors__name__regex=search_name_author)
        return queryset
    
    def _filter_by_title(self, request, queryset):
        search_title = request.GET.get('title')
        if search_title is not None:
            search_title_type = request.GET.get('title_type')
            search_title_type = "classique" if search_title_type is None else search_title_type
            
            if search_title_type == "classique":
                queryset = queryset.filter(title__icontains=search_title)
            else:
                queryset = queryset.filter(title__regex=search_title)
        return queryset
    
    def _filter_by_keyword(self, request, queryset, language):
        search_keyword = request.GET.get('keyword')
        if search_keyword is not None:
            search_keywords_type = request.GET.get('keyword_type')
            search_method = 'icontains' if search_keywords_type == 'classique' else 'regex'
            
            # Define language-specific filters
            filters = {
                'en': {'keywordbookenglish__keyword__token__{}'.format(search_method): search_keyword},
                'fr': {'keywordbookfrench__keyword__token__{}'.format(search_method): search_keyword},
            }
            
            # Apply language-specific filter or both if language is not specified
            if language in filters:
                queryset = queryset.filter(**filters[language])
            else:
                # For other languages or no language specified, search in both English and French
                english_filter = Q(**{'keywordbookenglish__keyword__token__{}'.format(search_method): search_keyword})
                french_filter = Q(**{'keywordbookfrench__keyword__token__{}'.format(search_method): search_keyword})
                queryset = queryset.filter(english_filter | french_filter)
        return queryset
    
    def _apply_sorting(self, request, queryset):
        sort = request.GET.get('sort')
        if sort == 'download_count':
            ord = request.GET.get('order')
            ord = "descending" if ord is None else ord
            if ord == "descending":
                queryset = queryset.order_by('-download_count')
            else:
                queryset = queryset.order_by('download_count')
        return queryset

        
    
class NeighboorsBook(APIView):
    def get_object(self, pk):
        try:
            return Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            raise Http404
    def get(self, request, pk, format=None):
        start_time = time.time()  # Start timing
        book = self.get_object(pk)
        try:
            book_voisins = Neighbors.objects.get(book=book)
        except Neighbors.DoesNotExist:
            return Response([])

        voisins = book_voisins.neighbors.all()
        serializer = BookSerializer(voisins, many=True)
        execution_time = time.time() - start_time
        print(f"NeighboorsBook query execution time: {execution_time:.4f} seconds")
        return Response(serializer.data)    

class CosinusViewSet(APIView):
    """
    API view for cosine similarity search that follows the same structure as BookViewSet.
    """
    
    def get(self, request, format=None):
        # Start with the same queryset as BookViewSet
        queryset = Book.objects.exclude(download_count__isnull=True)
        queryset = queryset.exclude(title__isnull=True)
        
        # Get language filter
        language = request.GET.get('languages')
        if language is not None:
            queryset = queryset.filter(languages__code=language)
        
        # Convert language code to format used by cosine similarity
        lang_mapping = {'en': 'english', 'fr': 'french'}
        search_language = 'both'
        if language in lang_mapping:
            search_language = lang_mapping[language]
            
        # Author name filter (same as BookViewSet)
        search_name_author = request.GET.get('author_name')
        if search_name_author is not None:
            search_name_authors_type = request.GET.get('author_name_type')
            search_name_authors_type = "classique" if search_name_authors_type is None else search_name_authors_type
            
            if search_name_authors_type == "classique":
                queryset = queryset.filter(authors__name__icontains=search_name_author)
            else:
                queryset = queryset.filter(authors__name__regex=search_name_author)
        
        # Title filter (same as BookViewSet)
        search_title = request.GET.get('title')
        if search_title is not None:
            search_title_type = request.GET.get('title_type')
            search_title_type = "classique" if search_title_type is None else search_title_type
            
            if search_title_type == "classique":
                queryset = queryset.filter(title__icontains=search_title)
            else:
                queryset = queryset.filter(title__regex=search_title)
        
        # Keyword search with cosine similarity
        search_keyword = request.GET.get('keyword')
        if search_keyword is None:
            # If no keyword is provided, just return the filtered queryset
            queryset = queryset.distinct()
            serializer = BookSerializer(queryset, many=True)
            return Response(serializer.data)
        
        # Get parameters for cosine search
        search_keywords_type = request.GET.get('keyword_type', 'classique')
        top_n = int(request.GET.get('top', 10))
        min_score = float(request.GET.get('min_score', 0.3))
        
        # Get base book IDs from the filtered queryset
        base_book_ids = set(queryset.values_list('gutenberg_id', flat=True))
        
        # Determine search method based on search_type
        search_method = 'icontains' if search_keywords_type == 'classique' else 'regex'
        
        # Find keyword objects with the specified term
        keyword_objects = []
        
        if search_language in ['english', 'both']:
            filter_kwargs = {f'token__{search_method}': search_keyword}
            english_keywords = KeywordsEnglish.objects.filter(**filter_kwargs)
            keyword_objects.extend([(kw, 'english') for kw in english_keywords])
        
        if search_language in ['french', 'both']:
            filter_kwargs = {f'token__{search_method}': search_keyword}
            french_keywords = KeywordsFrench.objects.filter(**filter_kwargs)
            keyword_objects.extend([(kw, 'french') for kw in french_keywords])
        
        if not keyword_objects:
            return Response([])
        
        # Find books containing these keywords
        books_with_keywords = []
        books_details = {}
        
        for kw, lang in keyword_objects:
            if lang == 'english':
                books = Book.objects.filter(keywordbookenglish__keyword=kw)
                book_keywords = KeywordBookEnglish.objects.filter(keyword=kw).select_related('book')
            else:
                books = Book.objects.filter(keywordbookfrench__keyword=kw)
                book_keywords = KeywordBookFrench.objects.filter(keyword=kw).select_related('book')
            
            for book in books:
                # Only include books that passed the initial filters
                if book.gutenberg_id not in base_book_ids:
                    continue
                    
                if book.gutenberg_id not in books_details:
                    books_with_keywords.append(book)
                    books_details[book.gutenberg_id] = {
                        "book": book,
                        "keywords": defaultdict(float),
                        "similarity_score": 1.0  # Source books have perfect similarity
                    }
                
                # Store TF-IDF score for this book-keyword pair
                if lang == 'english':
                    try:
                        score = KeywordBookEnglish.objects.get(book=book, keyword=kw).tfidf_score
                    except KeywordBookEnglish.DoesNotExist:
                        score = 0.0
                else:
                    try:
                        score = KeywordBookFrench.objects.get(book=book, keyword=kw).tfidf_score
                    except KeywordBookFrench.DoesNotExist:
                        score = 0.0
                
                books_details[book.gutenberg_id]["keywords"][f"{lang}_{kw.token}"] = score
        
        if not books_with_keywords:
            return Response([])
        
        # Compute all unique keywords
        all_keywords = set()
        for book_id, details in books_details.items():
            all_keywords.update(details["keywords"].keys())
        
        all_keywords = list(all_keywords)
        
        # Create vector representations for each book
        book_vectors = {}
        for book_id, details in books_details.items():
            vector = [details["keywords"].get(kw, 0.0) for kw in all_keywords]
            book_vectors[book_id] = vector
        
        # Find all books that are similar to the ones containing the keyword
        similar_book_ids = set()
        for source_id, source_details in books_details.items():
            source_vector = book_vectors[source_id]
            
            # Skip if the source vector is all zeros
            if sum(source_vector) == 0:
                continue
                
            source_norm = np.linalg.norm(source_vector)
            if source_norm == 0:
                continue
            
            # Add the source book itself
            similar_book_ids.add(source_id)
            
            # Find books in the database that share keywords with this book
            shared_books = set()
            for kw_key, score in source_details["keywords"].items():
                if score <= 0:
                    continue
                    
                lang, token = kw_key.split('_', 1)
                
                if lang == 'english':
                    try:
                        keyword_obj = KeywordsEnglish.objects.get(token=token)
                        book_ids = KeywordBookEnglish.objects.filter(
                            keyword=keyword_obj, 
                            book_id__in=base_book_ids
                        ).values_list('book_id', flat=True)
                        shared_books.update(book_ids)
                    except KeywordsEnglish.DoesNotExist:
                        pass
                else:  # french
                    try:
                        keyword_obj = KeywordsFrench.objects.get(token=token)
                        book_ids = KeywordBookFrench.objects.filter(
                            keyword=keyword_obj,
                            book_id__in=base_book_ids
                        ).values_list('book_id', flat=True)
                        shared_books.update(book_ids)
                    except KeywordsFrench.DoesNotExist:
                        pass
            
            # Remove the source book
            if source_id in shared_books:
                shared_books.remove(source_id)
            
            # For each shared book, compute similarity
            for target_id in shared_books:
                if target_id in books_details:
                    # We've already calculated vectors for this book
                    target_vector = book_vectors[target_id]
                else:
                    # Need to build vector for this book
                    target_keywords = defaultdict(float)
                    
                    if search_language in ['english', 'both']:
                        english_kws = KeywordBookEnglish.objects.filter(book_id=target_id).select_related('keyword')
                        for kw_book in english_kws:
                            token = kw_book.keyword.token
                            keyword_key = f"english_{token}"
                            if keyword_key in all_keywords:  # Only include keywords we've seen
                                target_keywords[keyword_key] = kw_book.tfidf_score
                    
                    if search_language in ['french', 'both']:
                        french_kws = KeywordBookFrench.objects.filter(book_id=target_id).select_related('keyword')
                        for kw_book in french_kws:
                            token = kw_book.keyword.token
                            keyword_key = f"french_{token}"
                            if keyword_key in all_keywords:  # Only include keywords we've seen
                                target_keywords[keyword_key] = kw_book.tfidf_score
                    
                    target_vector = [target_keywords.get(kw, 0.0) for kw in all_keywords]
                
                target_norm = np.linalg.norm(target_vector)
                if target_norm == 0:
                    continue
                
                # Compute cosine similarity
                dot_product = np.dot(source_vector, target_vector)
                similarity = dot_product / (source_norm * target_norm)
                
                # If similarity is above threshold, add to results
                if similarity >= min_score:
                    similar_book_ids.add(target_id)
                    
                    # Store the details if not already present
                    if target_id not in books_details:
                        try:
                            target_book = Book.objects.get(gutenberg_id=target_id)
                            books_details[target_id] = {
                                "book": target_book,
                                "keywords": target_keywords,
                                "similarity_score": similarity
                            }
                        except Book.DoesNotExist:
                            continue
                    else:
                        # Update with highest similarity score
                        current_score = books_details[target_id].get("similarity_score", 0.0)
                        if similarity > current_score:
                            books_details[target_id]["similarity_score"] = similarity
        
        # Sort books by similarity score (descending)
        sorted_books = []
        for book_id in similar_book_ids:
            if book_id in books_details:
                details = books_details[book_id]
                sorted_books.append((details["book"], details.get("similarity_score", 0.0)))
        
        sorted_books.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to top_n results if specified
        if top_n > 0:
            sorted_books = sorted_books[:top_n]
        
        # Apply sort from BookViewSet if requested
        sort = request.GET.get('sort')
        if sort == 'download_count':
            ord = request.GET.get('order')
            ord = "descending" if ord is None else ord
            
            # Extract book IDs in the current order
            book_ids_order = [book.gutenberg_id for book, _ in sorted_books]
            
            # Apply ordering to the books that passed cosine similarity
            if ord == "descending":
                sorted_queryset = Book.objects.filter(gutenberg_id__in=book_ids_order).order_by('-download_count')
            else:
                sorted_queryset = Book.objects.filter(gutenberg_id__in=book_ids_order).order_by('download_count')
                
            # Extract the books in the new order
            final_books = list(sorted_queryset)
        else:
            # Use cosine similarity ordering
            final_books = [book for book, _ in sorted_books]
        
        # Serialize and return the results
        serializer = BookSerializer(final_books, many=True)
        return Response(serializer.data)
    """
    API view for cosine similarity search that follows the same structure as BookViewSet.
    """
    
    def get(self, request, format=None):
        # Start with the same queryset as BookViewSet
        queryset = Book.objects.exclude(download_count__isnull=True)
        queryset = queryset.exclude(title__isnull=True)
        
        # Get language filter
        language = request.GET.get('languages')
        if language is not None:
            queryset = queryset.filter(languages__code=language)
        
        # Convert language code to format used by cosine similarity
        lang_mapping = {'en': 'english', 'fr': 'french'}
        search_language = 'both'
        if language in lang_mapping:
            search_language = lang_mapping[language]
            
        # Author name filter (same as BookViewSet)
        search_name_author = request.GET.get('author_name')
        if search_name_author is not None:
            search_name_authors_type = request.GET.get('author_name_type')
            search_name_authors_type = "classique" if search_name_authors_type is None else search_name_authors_type
            
            if search_name_authors_type == "classique":
                queryset = queryset.filter(authors__name__icontains=search_name_author)
            else:
                queryset = queryset.filter(authors__name__regex=search_name_author)
        
        # Title filter (same as BookViewSet)
        search_title = request.GET.get('title')
        if search_title is not None:
            search_title_type = request.GET.get('title_type')
            search_title_type = "classique" if search_title_type is None else search_title_type
            
            if search_title_type == "classique":
                queryset = queryset.filter(title__icontains=search_title)
            else:
                queryset = queryset.filter(title__regex=search_title)
        
        # Keyword search with cosine similarity
        search_keyword = request.GET.get('keyword')
        if search_keyword is None:
            # If no keyword is provided, just return the filtered queryset
            queryset = queryset.distinct()
            serializer = BookSerializer(queryset, many=True)
            return Response(serializer.data)
        
        # Get parameters for cosine search
        search_keywords_type = request.GET.get('keyword_type', 'classique')
        top_n = int(request.GET.get('top', 10))
        min_score = float(request.GET.get('min_score', 0.3))
        
        # Get base book IDs from the filtered queryset
        base_book_ids = set(queryset.values_list('gutenberg_id', flat=True))
        
        # Determine search method based on search_type
        search_method = 'icontains' if search_keywords_type == 'classique' else 'regex'
        
        # Find keyword objects with the specified term
        keyword_objects = []
        
        if search_language in ['english', 'both']:
            filter_kwargs = {f'token__{search_method}': search_keyword}
            english_keywords = KeywordsEnglish.objects.filter(**filter_kwargs)
            keyword_objects.extend([(kw, 'english') for kw in english_keywords])
        
        if search_language in ['french', 'both']:
            filter_kwargs = {f'token__{search_method}': search_keyword}
            french_keywords = KeywordsFrench.objects.filter(**filter_kwargs)
            keyword_objects.extend([(kw, 'french') for kw in french_keywords])
        
        if not keyword_objects:
            return Response([])
        
        # Find books containing these keywords
        books_with_keywords = []
        books_details = {}
        
        for kw, lang in keyword_objects:
            if lang == 'english':
                books = Book.objects.filter(keywordbookenglish__keyword=kw)
                book_keywords = KeywordBookEnglish.objects.filter(keyword=kw).select_related('book')
            else:
                books = Book.objects.filter(keywordbookfrench__keyword=kw)
                book_keywords = KeywordBookFrench.objects.filter(keyword=kw).select_related('book')
            
            for book in books:
                # Only include books that passed the initial filters
                if book.gutenberg_id not in base_book_ids:
                    continue
                    
                if book.gutenberg_id not in books_details:
                    books_with_keywords.append(book)
                    books_details[book.gutenberg_id] = {
                        "book": book,
                        "keywords": defaultdict(float),
                        "similarity_score": 1.0  # Source books have perfect similarity
                    }
                
                # Store TF-IDF score for this book-keyword pair
                if lang == 'english':
                    try:
                        score = KeywordBookEnglish.objects.get(book=book, keyword=kw).tfidf_score
                    except KeywordBookEnglish.DoesNotExist:
                        score = 0.0
                else:
                    try:
                        score = KeywordBookFrench.objects.get(book=book, keyword=kw).tfidf_score
                    except KeywordBookFrench.DoesNotExist:
                        score = 0.0
                
                books_details[book.gutenberg_id]["keywords"][f"{lang}_{kw.token}"] = score
        
        if not books_with_keywords:
            return Response([])
        
        # Compute all unique keywords
        all_keywords = set()
        for book_id, details in books_details.items():
            all_keywords.update(details["keywords"].keys())
        
        all_keywords = list(all_keywords)
        
        # Create vector representations for each book
        book_vectors = {}
        for book_id, details in books_details.items():
            vector = [details["keywords"].get(kw, 0.0) for kw in all_keywords]
            book_vectors[book_id] = vector
        
        # Find all books that are similar to the ones containing the keyword
        similar_book_ids = set()
        for source_id, source_details in books_details.items():
            source_vector = book_vectors[source_id]
            
            # Skip if the source vector is all zeros
            if sum(source_vector) == 0:
                continue
                
            source_norm = np.linalg.norm(source_vector)
            if source_norm == 0:
                continue
            
            # Add the source book itself
            similar_book_ids.add(source_id)
            
            # Find books in the database that share keywords with this book
            shared_books = set()
            for kw_key, score in source_details["keywords"].items():
                if score <= 0:
                    continue
                    
                lang, token = kw_key.split('_', 1)
                
                if lang == 'english':
                    try:
                        keyword_obj = KeywordsEnglish.objects.get(token=token)
                        book_ids = KeywordBookEnglish.objects.filter(
                            keyword=keyword_obj, 
                            book_id__in=base_book_ids
                        ).values_list('book_id', flat=True)
                        shared_books.update(book_ids)
                    except KeywordsEnglish.DoesNotExist:
                        pass
                else:  # french
                    try:
                        keyword_obj = KeywordsFrench.objects.get(token=token)
                        book_ids = KeywordBookFrench.objects.filter(
                            keyword=keyword_obj,
                            book_id__in=base_book_ids
                        ).values_list('book_id', flat=True)
                        shared_books.update(book_ids)
                    except KeywordsFrench.DoesNotExist:
                        pass
            
            # Remove the source book
            if source_id in shared_books:
                shared_books.remove(source_id)
            
            # For each shared book, compute similarity
            for target_id in shared_books:
                if target_id in books_details:
                    # We've already calculated vectors for this book
                    target_vector = book_vectors[target_id]
                else:
                    # Need to build vector for this book
                    target_keywords = defaultdict(float)
                    
                    if search_language in ['english', 'both']:
                        english_kws = KeywordBookEnglish.objects.filter(book_id=target_id).select_related('keyword')
                        for kw_book in english_kws:
                            token = kw_book.keyword.token
                            keyword_key = f"english_{token}"
                            if keyword_key in all_keywords:  # Only include keywords we've seen
                                target_keywords[keyword_key] = kw_book.tfidf_score
                    
                    if search_language in ['french', 'both']:
                        french_kws = KeywordBookFrench.objects.filter(book_id=target_id).select_related('keyword')
                        for kw_book in french_kws:
                            token = kw_book.keyword.token
                            keyword_key = f"french_{token}"
                            if keyword_key in all_keywords:  # Only include keywords we've seen
                                target_keywords[keyword_key] = kw_book.tfidf_score
                    
                    target_vector = [target_keywords.get(kw, 0.0) for kw in all_keywords]
                
                target_norm = np.linalg.norm(target_vector)
                if target_norm == 0:
                    continue
                
                # Compute cosine similarity
                dot_product = np.dot(source_vector, target_vector)
                similarity = dot_product / (source_norm * target_norm)
                
                # If similarity is above threshold, add to results
                if similarity >= min_score:
                    similar_book_ids.add(target_id)
                    
                    # Store the details if not already present
                    if target_id not in books_details:
                        try:
                            target_book = Book.objects.get(gutenberg_id=target_id)
                            books_details[target_id] = {
                                "book": target_book,
                                "keywords": target_keywords,
                                "similarity_score": similarity
                            }
                        except Book.DoesNotExist:
                            continue
                    else:
                        # Update with highest similarity score
                        current_score = books_details[target_id].get("similarity_score", 0.0)
                        if similarity > current_score:
                            books_details[target_id]["similarity_score"] = similarity
        
        # Sort books by similarity score (descending)
        sorted_books = []
        for book_id in similar_book_ids:
            if book_id in books_details:
                details = books_details[book_id]
                sorted_books.append((details["book"], details.get("similarity_score", 0.0)))
        
        sorted_books.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to top_n results if specified
        if top_n > 0:
            sorted_books = sorted_books[:top_n]
        
        # Apply sort from BookViewSet if requested
        sort = request.GET.get('sort')
        if sort == 'download_count':
            ord = request.GET.get('order')
            ord = "descending" if ord is None else ord
            
            # Extract book IDs in the current order
            book_ids_order = [book.gutenberg_id for book, _ in sorted_books]
            
            # Apply ordering to the books that passed cosine similarity
            if ord == "descending":
                sorted_queryset = Book.objects.filter(gutenberg_id__in=book_ids_order).order_by('-download_count')
            else:
                sorted_queryset = Book.objects.filter(gutenberg_id__in=book_ids_order).order_by('download_count')
                
            # Extract the books in the new order
            final_books = list(sorted_queryset)
        else:
            # Use cosine similarity ordering
            final_books = [book for book, _ in sorted_books]
        
        # Serialize and return the results
        serializer = BookSerializer(final_books, many=True)
        return Response(serializer.data)