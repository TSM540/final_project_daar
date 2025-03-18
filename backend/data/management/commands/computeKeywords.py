from django.core.management.base import BaseCommand
from data.models import Book
import spacy
import os
from collections import Counter
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Extract keywords from books'

    def add_arguments(self, parser):
        parser.add_argument('--batch_size', type=int, default=1000, help='Batch size for text processing')
        parser.add_argument('--max_workers', type=int, default=4, help='Maximum number of worker threads')

    def handle(self, *args, **options):
        # Load models once
        nlp = {
            'en': spacy.load('en_core_web_sm', disable=['parser', 'ner']), 
            'fr': spacy.load('fr_core_news_sm', disable=['parser', 'ner'])
        }
        
        # Create output directory if it doesn't exist
        os.makedirs("./keywords/", exist_ok=True)
        
        # Get all books at once to avoid multiple DB queries
        books = list(Book.objects.all().prefetch_related('languages'))
        
        with ThreadPoolExecutor(max_workers=options['max_workers']) as executor:
            futures = []
            for book in books:
                futures.append(
                    executor.submit(
                        self.process_book, 
                        book, 
                        nlp, 
                        options['batch_size']
                    )
                )
            
            # Process with progress bar
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing books"):
                try:
                    future.result()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing book: {e}"))
    
    def process_book(self, book, nlp_models, batch_size):
        try:
            # Get language code
            languages = list(book.languages.all())
            if not languages:
                return
            
            code = languages[0].code
            if code not in ['en', 'fr']:
                return
                
            str_pk = str(book.pk)
            chemin_fichier = os.path.join('books', f"{str_pk}.txt")
            
            # Check if file exists
            if not os.path.exists(chemin_fichier):
                return
                
            # Process in batches to avoid memory issues
            keywords_counter = Counter()
            
            with open(chemin_fichier, "r", encoding='utf-8') as fichier:
                document = fichier.read()
                
            # Split into paragraphs
            texts = document.split("\n\n")
            
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                batch_text = " ".join(batch)
                
                # Process with spaCy
                doc = nlp_models[code](batch_text)
                
                # Extract keywords more efficiently
                batch_keywords = [
                    token.lemma_.casefold() 
                    for token in doc 
                    if token.is_alpha and not token.is_stop
                ]
                
                # Update counter
                keywords_counter.update(batch_keywords)
            
            # Save results
            output_path = os.path.join("./keywords/", f"{str_pk}.json")
            with open(output_path, "w") as fichier:
                json.dump(keywords_counter, fichier)
                
        except Exception as e:
            raise Exception(f"Error processing book {book.pk}: {str(e)}")