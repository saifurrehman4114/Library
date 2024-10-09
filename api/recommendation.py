import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Book, FavoriteBook

def get_recommendations(user):
    # Get user's favorite books
    favorite_books = FavoriteBook.objects.filter(user=user).select_related('book')
    if not favorite_books:
        return []

    # Prepare data for TF-IDF
    books_df = pd.DataFrame(list(Book.objects.values('id', 'title', 'author__name', 'genre')))
    books_df['content'] = books_df['title'] + ' ' + books_df['author__name'] + ' ' + books_df['genre']

    # TF-IDF Vectorization
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(books_df['content'])

    # Get indices of user's favorite books
    favorite_indices = books_df[books_df['id'].isin([fb.book.id for fb in favorite_books])].index

    # Calculate mean TF-IDF vector for favorite books
    user_profile = tfidf_matrix[favorite_indices].mean(axis=0)

    # Calculate cosine similarity between user profile and all books
    cosine_similarities = cosine_similarity(user_profile, tfidf_matrix).flatten()

    # Get top 5 similar books (excluding favorites)
    similar_indices = cosine_similarities.argsort()[::-1]
    recommended_indices = [idx for idx in similar_indices if idx not in favorite_indices][:5]

    # Get recommended book IDs
    recommended_ids = books_df.iloc[recommended_indices]['id'].tolist()

    # Return recommended Book objects
    return Book.objects.filter(id__in=recommended_ids)