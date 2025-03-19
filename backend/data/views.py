from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.http import Http404
from data.models import Book, Neighbors, KeywordsEnglish, KeywordsFrench
from data.serializers import BookSerializer
from django.db.models import Q

# Create your views here.


class BookViewSet(APIView):
    
    def get(self, request, format=None):
        queryset = Book.objects.exclude(download_count__isnull=True)
        queryset = queryset.exclude(title__isnull=True)
        print(request)
        language = request.GET.get('languages')
        if language is not None:
            queryset = queryset.filter(languages__code=language)
        print(language)
        search_name_author = request.GET.get('author_name')
        if search_name_author is not None:
            search_name_authors_type = request.GET.get('author_name_type')
            search_name_authors_type = "classique" if search_name_authors_type is None else search_name_authors_type
            
            if search_name_authors_type == "classique":
                queryset = queryset.filter(authors__name__icontains=search_name_author)
            else:
                queryset = queryset.filter(authors__name__regex=search_name_author)
                
        search_title = request.GET.get('title')
        if search_title is not None:
            search_title_type = request.GET.get('title_type')
            
            search_title_type = "classique" if search_title_type is None else search_title_type
            if search_title_type == "classique":
                queryset = queryset.filter(title__icontains=search_title)
            else:
                queryset = queryset.filter(title__regex=search_title)
                
        search_keyword = request.GET.get('keyword')
        print(KeywordsEnglish.objects.filter(keywordbookenglish__keyword__token__regex=search_keyword))
        if search_keyword is not None:
            search_keywords_type = request.GET.get('keyword_type')
            search_method = 'icontains' if search_keywords_type == 'classique' else 'regex'
            
            # Define language-specific filters
            filters = {
                'en': {'keywordbookenglish__keyword__token__{}'.format(search_method): search_keyword},
                'fr': {'keywordbookfrench__keyword__token__{}'.format(search_method): search_keyword},
            }
            
            # Apply language-specific filter or both if language is not specified
            print(filters)
            if language in filters:
                queryset = queryset.filter(**filters[language])
            else:
                # For other languages or no language specified, search in both English and French
                english_filter = Q(**{'keywordbookenglish__keyword__token__{}'.format(search_method): search_keyword})
                french_filter = Q(**{'keywordbookfrench__keyword__token__{}'.format(search_method): search_keyword})
                queryset = queryset.filter(english_filter | french_filter)

        queryset = queryset.distinct()
        sort = request.GET.get('sort')
        if sort == 'download_count':
            ord = request.GET.get('order')
            ord = "descending" if ord is None else ord
            if ord == "descending":
                queryset = queryset.order_by('-download_count')
            else:
                queryset = queryset.order_by('download_count')    
            
        queryset.distinct()
        serializer = BookSerializer(queryset, many=True)
        return Response(serializer.data)

        
    
class NeighboorsBook(APIView):
    def get_object(self, pk):
        try:
            return Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            raise Http404
    def get(self, request, pk, format=None):
        book = self.get_object(pk)
        try:
            book_voisins = Neighbors.objects.get(book=book)
        except Neighbors.DoesNotExist:
            return Response([])

        voisins = book_voisins.neighbors.all()
        serializer = BookSerializer(voisins, many=True)
        return Response(serializer.data)    
    