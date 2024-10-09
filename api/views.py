from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from .models import Author, Book, FavoriteBook
from .serializers import UserSerializer, AuthorSerializer, BookSerializer, FavoriteBookSerializer
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from pathlib import Path
import json

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['title', 'author__name']
    search_fields = ['title', 'author__name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()

# Load the dataset only once when the application starts
BASE_DIR = Path(__file__).resolve().parent.parent
BOOKS_JSON_PATH = os.path.join(BASE_DIR, 'books.json')

# Load the dataset once at the start
with open(BOOKS_JSON_PATH, 'r', encoding='utf-8') as f:
    books_data = json.load(f)

# Convert the loaded JSON data to a DataFrame
df = pd.json_normalize(books_data)

# Combine the relevant fields into a single feature for better TF-IDF performance
df['features'] = df['title'] + ' ' + df['authors'].fillna('') + ' ' + df['categories'].fillna('')

class FavoriteBookViewSet(viewsets.ModelViewSet):
    queryset = FavoriteBook.objects.all()
    serializer_class = FavoriteBookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteBook.objects.filter(user=self.request.user)

    @action(detail=False, methods=['GET'])
    def recommendations(self, request):
        user_favorites = FavoriteBook.objects.filter(user=request.user)

        if not user_favorites:
            return Response({"detail": "No favorite books found."}, status=status.HTTP_404_NOT_FOUND)

        # Extract the favorite books' ISBNs
        favorite_isbns = [fav.book.isbn for fav in user_favorites]

        # Get the indices of the user's favorite books from the dataset
        favorite_indices = df[df['isbn'].isin(favorite_isbns)].index

        # Create a TF-IDF vectorizer
        tfidf = TfidfVectorizer(stop_words='english')

        # Transform the features for TF-IDF
        tfidf_matrix = tfidf.fit_transform(df['features'])

        # Calculate the average feature vector of the user's favorite books
        user_profile = tfidf_matrix[favorite_indices].mean(axis=0)

        # Calculate cosine similarity between the user profile and all books
        cosine_similarities = cosine_similarity(user_profile, tfidf_matrix).flatten()

        # Get indices of the top 5 most similar books excluding the favorites
        similar_indices = cosine_similarities.argsort()[::-1]
        similar_indices = [idx for idx in similar_indices if idx not in favorite_indices][:5]

        # Fetch recommended books
        recommended_books = df.iloc[similar_indices]

        # Prepare the response
        recommendations = [
            {
                'title': book['title'],
                'author': book['authors'],
                'isbn': book['isbn']
            }
            for _, book in recommended_books.iterrows()
        ]

        return Response(recommendations)
