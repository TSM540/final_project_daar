from data import views
from django.urls import path
from backend.config import *
from data.config import *


def construct_url_data(url):
    return URL_BASE_DATA + url

urlpatterns = [
    path('data/books', views.BookViewSet.as_view()),
    path('data/books/neighbors/<int:pk>', views.NeighboorsBook.as_view()),
    path('data/books/keywords/cosine-similarity/', views.CosinusViewSet.as_view()),
    path('server/books/', views.BooksList.as_view())
]