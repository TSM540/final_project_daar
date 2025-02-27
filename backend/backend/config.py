URL_BASE = 'http://localhost:8000/'
URL_SEARCH_BOOKS = 'books/'
URL_NEIGHBOR = "books/neighbors/<int:pk>"

def construct_url_requete_search(url : str) -> str:
    return url.split('<')[0]