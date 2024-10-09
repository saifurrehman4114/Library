from django.contrib import admin
from .models import Author, Book, FavoriteBook

admin.site.register(Author)
admin.site.register(Book)
admin.site.register(FavoriteBook)

# api/apps.py
from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'