from django.core.management.base import BaseCommand
from data.models import *
import json
import requests
import re
from data.config import URL_INIT_BIBLIOTHEQUE, MIN_NB_LIVRE_BIBLIOTHEQUE, MIN_NB_MOTS_LIVRES
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

DOM = '\ufeff'
dossier_book = "books/"

def compter_mots(url_du_livre, max_retries=3):
    """Télécharge le livre et compte les mots avec une gestion des erreurs de connexion."""
    for attempt in range(max_retries):
        try:
            fichier = requests.get(url_du_livre, timeout=10, stream=True)  
            fichier.raise_for_status()
            contenu = fichier.text
            mots = re.findall(r'\b\w+\b', contenu)
            nombre_de_mots = len(mots)
            return contenu, nombre_de_mots
        except (requests.exceptions.RequestException, requests.exceptions.ChunkedEncodingError) as e:
            print(f"Tentative {attempt+1}/{max_retries} échouée: {e}")
            time.sleep(2)  # Attente avant une nouvelle tentative
    raise Exception(f"Impossible de télécharger {url_du_livre} après {max_retries} tentatives")



def put_book_db(book):
    """Make/update the book."""
    print(book['id'])
    book_in_db = Book.objects.create(
        gutenberg_id=book['id'],
        download_count=book['download_count'],
        title=book['title'],
        cover_image=book['formats']['image/jpeg'],
        plain_text=book['formats']['text/plain; charset=us-ascii']

    )

    """Make/update the authors."""

    authors = []
    for author in book['authors']:
        person = Person.objects.filter(
            name=author['name'],
            birth_year=author['birth_year'],
            death_year=author['death_year']
        )
        if person.exists():
            person = person[0]
        else:
            person = Person.objects.create(
                name=author['name'],
                birth_year=author['birth_year'],
                death_year=author['death_year']
            )
        authors.append(person)

    for author in authors:
        book_in_db.authors.add(author)

    ''' Make/update the languages. '''
    if book['languages']:  # Ensure the list is not empty
        first_language = book['languages'][0]  # Take only the first language
        language_in_db, created = Language.objects.get_or_create(code=first_language)
        book_in_db.languages.add(language_in_db)  # Add only the first language

    ''' Make/update subjects. '''

    subjects = []
    for subject in book['subjects']:
        subject_in_db = Subject.objects.filter(name=subject)
        if subject_in_db.exists():
            subject_in_db = subject_in_db[0]
        else:
            subject_in_db = Subject.objects.create(name=subject)
        subjects.append(subject_in_db)

    for subject in subjects:
        book_in_db.subjects.add(subject)



class Command(BaseCommand):
    help = 'Initialise the database'

    def handle(self, *args, **options):
        nb_livres = 0
        url = URL_INIT_BIBLIOTHEQUE
        if not os.path.exists(dossier_book):
            os.makedirs(dossier_book)

        while nb_livres < MIN_NB_LIVRE_BIBLIOTHEQUE:
            reponse = requests.get(url)
            json_data = reponse.json()

            with ThreadPoolExecutor(max_workers=5000) as executor:
                futures = {}

                for book in json_data['results']:
                    if book['languages'][0] == 'en' or book['languages'][0] == 'fr': 
                        # print(book['languages'][0])
                        # print(book['languages'])
                        # if book['languages'][0] in ['es','tl','enm','fy','la','nah']: 
                        #     continue 
                        if 'text/plain; charset=us-ascii' in book['formats']:
                            future = executor.submit(compter_mots, book['formats']['text/plain; charset=us-ascii'])
                            futures[future] = book

                for future in as_completed(futures):
                    book = futures[future]
                    try:
                        contenu, nb_mot = future.result()
                        if nb_mot >= MIN_NB_MOTS_LIVRES:
                            executor.submit(put_book_db, book)  #  Parallel DB insertion

                            # Nettoyage du contenu
                            if contenu and contenu[0] == DOM:
                                contenu = contenu[1:]

                            # Sauvegarde du livre en local
                            chemin_fichier = os.path.join(dossier_book, f"{book['id']}.txt")
                            with open(chemin_fichier, 'w', encoding="utf-8") as fichier:
                                fichier.write(contenu)

                            nb_livres += 1
                            self.stdout.write(self.style.SUCCESS(f'[{time.ctime()}] Successfully added book id="{book["id"]}"'))

                    except requests.exceptions.HTTPError:
                        self.stdout.write(' Request Exception\n')
                        continue
                    except KeyError as e:
                        print(f"Une KeyError s'est produite: {e}")
                        continue
                    except Exception as error:
                        book_json = json.dumps(book, indent=4)
                        self.stdout.write(f'Error while putting this book info in the database:\n{book_json}\n')
                        raise error

            if json_data['next'] is None:
                break
            url = json_data['next']

