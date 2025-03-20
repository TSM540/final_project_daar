import numpy as np
from django.core.management.base import BaseCommand
from django.db import transaction
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm
from data.models import Book, KeywordBookEnglish, KeywordsEnglish, KeywordBookFrench, KeywordsFrench

class Command(BaseCommand):
    help = "Compute and store TF-IDF scores for keywords in books"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size', 
            type=int, 
            default=1000,
            help='Number of books to process in each batch'
        )
        parser.add_argument(
            '--max-features', 
            type=int, 
            default=10000,
            help='Maximum number of features for TF-IDF vectorizer'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Starting TF-IDF computation..."))
        
        batch_size = options['batch_size']
        max_features = options['max_features']
        
        # Count total books for progress tracking
        total_books = Book.objects.count()
        if total_books == 0:
            self.stdout.write(self.style.WARNING("⚠️ No books found. Aborting."))
            return
            
        self.stdout.write(self.style.SUCCESS(f"📚 Found {total_books} books to process"))
        
        # Process books in batches
        for offset in tqdm(range(0, total_books, batch_size), desc="Processing batches"):
            self._process_batch(offset, batch_size, max_features)
            
        self.stdout.write(self.style.SUCCESS("✅ TF-IDF computation completed successfully!"))
    
    def _process_batch(self, offset, batch_size, max_features):
        # Get a batch of books
        books_batch = Book.objects.all()[offset:offset+batch_size]
        book_ids = [book.gutenberg_id for book in books_batch]
        
        # Prepare book texts dictionary
        book_texts = {book_id: "" for book_id in book_ids}
        
        # Fetch English keywords in bulk
        english_keywords = KeywordBookEnglish.objects.filter(
            book__gutenberg_id__in=book_ids
        ).select_related('keyword', 'book')
        
        # Fetch French keywords in bulk
        french_keywords = KeywordBookFrench.objects.filter(
            book__gutenberg_id__in=book_ids
        ).select_related('keyword', 'book')
        
        # Create document representations
        for kw_book in english_keywords:
            book_id = kw_book.book.gutenberg_id
            book_texts[book_id] += f" {kw_book.keyword.token}" * kw_book.occurence
            
        for kw_book in french_keywords:
            book_id = kw_book.book.gutenberg_id
            book_texts[book_id] += f" {kw_book.keyword.token}" * kw_book.occurence
        
        # Skip empty batch
        if not any(book_texts.values()):
            return
            
        # TF-IDF computation
        vectorizer = TfidfVectorizer(
            min_df=1,           # Inclut les termes qui apparaissent au moins une fois
            max_features=None,  # N'impose pas de limite sur les features
            norm='l2',          # Normalisation L2 (par défaut)
            use_idf=True,       # Utiliser l'IDF (par défaut)
            smooth_idf=True     # Ajouter 1 à tous les document frequencies (évite la division par zéro)
        )
        
        # Get book IDs and texts in consistent order
        book_ids_ordered = [bid for bid, text in book_texts.items() if text.strip()]
        texts_ordered = [book_texts[bid].strip() for bid in book_ids_ordered if book_texts[bid].strip()]
        
        # Skip if no valid texts
        if not texts_ordered:
            return
            
        tfidf_matrix = vectorizer.fit_transform(texts_ordered)
        feature_names = vectorizer.get_feature_names_out()
        
        # Create a {token: tf-idf score} mapping per book
        book_tfidf = {}
        for idx, book_id in enumerate(book_ids_ordered):
            book_tfidf[book_id] = {
                feature_names[i]: score 
                for i, score in enumerate(tfidf_matrix[idx].toarray()[0])
                if score > 0  # Only store non-zero scores
            }
        
        # Update TF-IDF scores in smaller batches
        with transaction.atomic():
            # Update English keywords
            self._update_keyword_scores(english_keywords, book_tfidf)
            
            # Update French keywords
            self._update_keyword_scores(french_keywords, book_tfidf)
    
    def _update_keyword_scores(self, keywords, book_tfidf, batch_size=1000):
        """Update TF-IDF scores in smaller batches"""
        updates = []
        
        for kw_book in keywords:
            book_id = kw_book.book.gutenberg_id
            token = kw_book.keyword.token
            kw_book.tfidf_score = book_tfidf.get(book_id, {}).get(token, 0.0)
            updates.append(kw_book)
            
            # Process in smaller batches to avoid memory issues
            if len(updates) >= batch_size:
                kw_book.__class__.objects.bulk_update(updates, ["tfidf_score"])
                updates = []
                
        # Process remaining updates
        if updates:
            kw_book.__class__.objects.bulk_update(updates, ["tfidf_score"])