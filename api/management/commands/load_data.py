import json
import ijson
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from api.models import Author, Book
from tqdm import tqdm
import gc

class Command(BaseCommand):
    help = 'Load large dataset from JSON files into SQLite database with low memory usage'

    def add_arguments(self, parser):
        parser.add_argument('--chunk-size', type=int, default=100, help='Number of records to process in each chunk')

    def handle(self, *args, **options):
        chunk_size = options['chunk_size']

        self.optimize_sqlite()
        self.load_authors(chunk_size)
        self.load_books(chunk_size)
        self.create_indexes()

        self.stdout.write(self.style.SUCCESS('Data loaded successfully!'))

    def optimize_sqlite(self):
        self.stdout.write('Optimizing SQLite...')
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode = OFF;')
            cursor.execute('PRAGMA synchronous = OFF;')
            cursor.execute('PRAGMA cache_size = -50000;')  # Use 50MB of cache
            cursor.execute('PRAGMA temp_store = MEMORY;')

    def load_authors(self, chunk_size):
        self.stdout.write('Loading authors...')
        with open('authors.json', 'rb') as f:
            parser = ijson.parse(f)
            authors = []
            for prefix, event, value in parser:
                if prefix == 'item' and event == 'start_map':
                    author = {}
                elif prefix.startswith('item.') and event == 'string':
                    key = prefix.split('.')[1]
                    author[key] = value
                elif prefix == 'item' and event == 'end_map':
                    authors.append(author)
                    if len(authors) >= chunk_size:
                        self.bulk_insert_authors(authors)
                        authors = []
                        gc.collect()  # Force garbage collection

            if authors:
                self.bulk_insert_authors(authors)

    def bulk_insert_authors(self, authors):
        with transaction.atomic():
            Author.objects.bulk_create([
                Author(
                    id=author['id'],
                    name=author['name'],
                    biography=author.get('biography', '')
                ) for author in authors
            ], ignore_conflicts=True)

    def load_books(self, chunk_size):
        self.stdout.write('Loading books...')
        with open('books.json', 'rb') as f:
            parser = ijson.parse(f)
            books = []
            for prefix, event, value in parser:
                if prefix == 'item' and event == 'start_map':
                    book = {}
                elif prefix.startswith('item.') and event == 'string':
                    key = prefix.split('.')[1]
                    book[key] = value
                elif prefix == 'item' and event == 'end_map':
                    books.append(book)
                    if len(books) >= chunk_size:
                        self.bulk_insert_books(books)
                        books = []
                        gc.collect()  # Force garbage collection

            if books:
                self.bulk_insert_books(books)

    def bulk_insert_books(self, books):
        with transaction.atomic():
            Book.objects.bulk_create([
                Book(
                    id=book['id'],
                    title=book['title'],
                    author_id=book['author_id'],
                    isbn=book['isbn'],
                    publication_date=book.get('publication_date'),
                    description=book.get('description', ''),
                    genre=book.get('genre', '')
                ) for book in books
            ], ignore_conflicts=True)

    def create_indexes(self):
        self.stdout.write('Creating indexes...')
        with connection.cursor() as cursor:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_book_title ON api_book (title);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_book_author ON api_book (author_id);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_book_isbn ON api_book (isbn);')