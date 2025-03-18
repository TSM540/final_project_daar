from django.core.management import BaseCommand
from data.models import *
import requests
from data.jaccard import jaccard_distance
import time
import json
import os
from tqdm import tqdm
import concurrent.futures
import threading

JACCARD_DISTANCE_THRESHOLD = 0.5

class Command(BaseCommand):
    help = 'Create the jaccard graph'
    
    # Adding a lock for thread safety
    lock = threading.Lock()

    def add_as_neighbor(self, pk1, pk2):
        l1 = Book.objects.get(pk=pk1)
        l2 = Book.objects.get(pk=pk2)
        
        # print('before')

        # Création ou récupération de l'entrée pour l1
        neighbor_entry1, created1 = Neighbors.objects.get_or_create(book=l1)
        neighbor_entry1.neighbors.add(l2)  # Ajout de l2 comme voisin de l1
        neighbor_entry1.save()

        # Création ou récupération de l'entrée pour l2
        neighbor_entry2, created2 = Neighbors.objects.get_or_create(book=l2)
        neighbor_entry2.neighbors.add(l1)  # Ajout de l1 comme voisin de l2
        neighbor_entry2.save()
        # print('after')
        self.stdout.write(self.style.SUCCESS(f'[{time.ctime()}] Successfully added the book {pk1} and book {pk2} as neighbors'))

    def process_book(self, pk, tokens, books_occurences, neighbor):
        book_neighbor = neighbor[pk]
        neighbors_found = []
        
        for pk2 in books_occurences.keys():
            if pk2 in book_neighbor or pk == pk2:
                continue
            if jaccard_distance(tokens, books_occurences[pk2]) < JACCARD_DISTANCE_THRESHOLD:
                # print(pk, pk2)
                with self.lock:
                    self.add_as_neighbor(pk, pk2)
                neighbors_found.append(pk2)
        
        # Update the neighbor dict with thread safety
        with self.lock:
            for pk2 in neighbors_found:
                if pk2 not in neighbor:
                    neighbor[pk2] = [pk]
                else:
                    neighbor[pk2].append(pk)
                    
        return pk
            
    def handle(self, *args, **options):
        books_occurences = dict()
        #using json file
        dossier_occu = "./keywords/"
        self.stdout.write('['+time.ctime()+'] Loading book data...')
        
        # Add tqdm for file loading
        for nom_fichier in tqdm(os.listdir(dossier_occu), desc="Loading files"):
            chemin_fichier = os.path.join(dossier_occu, nom_fichier)

            with open(chemin_fichier, "r") as fichier:
                token = json.load(fichier)
                
            pk = int(nom_fichier.split('.')[0])
            books_occurences[pk] = token
        

        self.stdout.write('['+time.ctime()+'] Creating the jaccard graph...')
        neighbor = {pk : [] for pk in books_occurences.keys()}
        
        # Use ThreadPoolExecutor to process books in parallel
        max_workers = min(32, len(books_occurences))  # Limit number of threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a list of futures
            futures = []
            for pk, tokens in books_occurences.items():
                future = executor.submit(self.process_book, pk, tokens, books_occurences, neighbor)
                futures.append(future)
            
            # Process results with progress bar
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing books"):
                pk = future.result()
                self.stdout.write(self.style.SUCCESS('['+time.ctime()+'] Successfully added the neighbors for book id="%s"' % pk))
                
        self.stdout.write('['+time.ctime()+'] End of Jaccard graph creation.')