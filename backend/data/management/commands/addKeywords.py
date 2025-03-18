from django.core.management.base import BaseCommand
from data.models import *
import os
import json
from tqdm import tqdm

dossier_occu = 'keywords'
MIN_OCCURENCE_THRESHOLD_FRENCH =10
MIN_OCCURENCE_THRESHOLD_ENGLISH =25
class Command(BaseCommand):
    help = 'add keywords'
    
    def handle(self, *args, **options):
        keywords = dict()
        keywords_code = {'en': set(), 'fr': set()}
        
        # Get list of files first, then use tqdm to show progress
        files = os.listdir(dossier_occu)
        self.stdout.write(f"Processing {len(files)} keyword files...")
        
        for nom_fichier in tqdm(files, desc="Reading keyword files"):
            chemin_fichier = os.path.join(dossier_occu, nom_fichier)
            pk = int(nom_fichier.split('.')[0])
            with open(chemin_fichier, 'r') as f:
                keywords_book = json.load(f)
                book = Book.objects.get(pk=pk)
            book_language_code = book.languages.all()[0].code
            for k, occ in keywords_book.items():
                if book_language_code == 'fr' and occ < MIN_OCCURENCE_THRESHOLD_FRENCH:
                    continue
                elif book_language_code == 'en' and occ < MIN_OCCURENCE_THRESHOLD_ENGLISH:
                    continue
                else:
                    if k not in keywords:
                        keywords_code[book_language_code].add(k)
                        keywords[k] = {(book, occ)}
                    else:
                        keywords[k].add((book, occ))
        self.stdout.write(f"Creating English keywords ({len(keywords_code['en'])} tokens)...")
        for k in tqdm(keywords_code['en'], desc="Creating English keywords"):
            key_en = KeywordsEnglish.objects.create(token=k)
            for (b, occu) in keywords[k]:
                KeywordBookEnglish.objects.create(book=b, occurence=occu, keyword=key_en)
                key_en.books.add(b)
        #to put back after treatement
        self.stdout.write(f"Creating French keywords ({len(keywords_code['fr'])} tokens)...")
        for k in tqdm(keywords_code['fr'], desc="Creating French keywords"):
            key_fr = KeywordsFrench.objects.create(token=k)
            for (b, occu) in keywords[k]:
                KeywordBookFrench.objects.create(book=b, occurence=occu, keyword=key_fr)
                key_fr.books.add(b)
        
      
        
        self.stdout.write(self.style.SUCCESS('Successfully added keywords'))