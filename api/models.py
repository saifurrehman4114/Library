from django.db import models
from django.contrib.auth.models import User

class Author(models.Model):
    name = models.CharField(max_length=100)
    biography = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    isbn = models.CharField(max_length=13, unique=True)
    publication_date = models.DateField()
    description = models.TextField(blank=True)
    genre = models.CharField(max_length=100, blank=True)  # New field for genre

    def __str__(self):
        return self.title


class FavoriteBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'book')