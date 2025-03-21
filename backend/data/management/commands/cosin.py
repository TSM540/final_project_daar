import numpy as np
from django.core.management.base import BaseCommand
from django.db.models import F, Q
from tqdm import tqdm
from collections import defaultdict
from data.models import Book, KeywordsEnglish, KeywordsFrench, KeywordBookEnglish, KeywordBookFrench
import time
# This is just a test file on your local machine, use it to test the cosine similarity between keywordds
# a good example would be to use sargon, comparing it to a normal search that takes  about 5-9 seconds depending on the database, this cosine similarity search should take about 1-2 seconds
class Command(BaseCommand):
    help = "Find books similar to those containing a specific keyword using cosine similarity"
    
    def add_arguments(self, parser):
        parser.add_argument(
            'keyword',
            type=str,
            help='Keyword to search for (e.g., "sargon")'
        )
        parser.add_argument(
            '--language',
            type=str,
            default='both',
            choices=['english', 'french', 'both'],
            help='Language to search in (default: both)'
        )
        parser.add_argument(
            '--top',
            type=int,
            default=10,
            help='Number of similar books to return per source book'
        )
        parser.add_argument(
            '--min-score',
            type=float,
            default=0.4,
            help='Minimum similarity score threshold'
        )
    
    def handle(self, *args, **options):
        start_time = time.time() 
        keyword = options['keyword'].lower()
        language = options['language']
        top_n = options['top']
        min_score = options['min_score']
        
        self.stdout.write(self.style.SUCCESS(f"🔍 Searching for books related to keyword: '{keyword}'"))
        
        # Find keyword objects with the specified term
        keyword_objects = []
        
        if language in ['english', 'both']:
            english_keywords = KeywordsEnglish.objects.filter(token__icontains=keyword)
            keyword_objects.extend([(kw, 'english') for kw in english_keywords])
        
        if language in ['french', 'both']:
            french_keywords = KeywordsFrench.objects.filter(token__icontains=keyword)
            keyword_objects.extend([(kw, 'french') for kw in french_keywords])
        
        if not keyword_objects:
            self.stdout.write(self.style.WARNING(f"⚠️ No keyword found containing '{keyword}'. Try a different term."))
            return
        
        self.stdout.write(self.style.SUCCESS(f"✅ Found {len(keyword_objects)} matching keywords"))
        
        # Find books containing these keywords
        books_by_keyword = {}
        for kw, lang in keyword_objects:
            if lang == 'english':
                books = Book.objects.filter(keywordbookenglish__keyword=kw).values_list('gutenberg_id', 'title')
                relationship = "KeywordBookEnglish"
            else:
                books = Book.objects.filter(keywordbookfrench__keyword=kw).values_list('gutenberg_id', 'title')
                relationship = "KeywordBookFrench"
            
            book_count = len(books)
            if book_count:
                books_by_keyword[f"{kw.token} ({lang})"] = {
                    "relationship": relationship,
                    "count": book_count,
                    "books": [{"id": book_id, "title": title} for book_id, title in books]
                }
        
        if not books_by_keyword:
            self.stdout.write(self.style.WARNING(f"⚠️ No books found containing the keyword '{keyword}'"))
            return
        
        # Display results
        self.stdout.write(self.style.SUCCESS("\n📊 Results:"))
        
        for keyword, data in books_by_keyword.items():
            self.stdout.write(f"\n🔑 Keyword: {keyword}")
            self.stdout.write(f"📚 Found in {data['count']} books through {data['relationship']} relationship")
            
            for i, book in enumerate(data['books'][:5], 1):  # Show only first 5 books
                self.stdout.write(f"  {i}. {book['title']} (ID: {book['id']})")
            
            if data['count'] > 5:
                self.stdout.write(f"  ... and {data['count'] - 5} more books")
        execution_time = time.time() - start_time
        print(f"Cosin query execution time: {execution_time:.4f} seconds")
        self.stdout.write(self.style.SUCCESS("\n✅ Search completed!"))