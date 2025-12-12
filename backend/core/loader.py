"""
core/loader.py

Role: Loader module to fetch books from the database and populate the DSA engine.
- Ensures in-memory structures (AVL, HashTable, Trie) are ready at application startup.
- Keeps backend DSA-first approach high-level and presentation-ready.
"""

from sqlalchemy.orm import Session
from models import Book
from core.engine import DSAEngine

# Singleton DSA Engine for the entire application
dsa_engine = DSAEngine()


def load_books_from_db(db: Session):
    """
    Load all books from the database into DSA structures
    :param db: SQLAlchemy session
    """
    # Fetch all books from DB
    books = db.query(Book).all()

    # Populate DSA engine (AVL, Hash, Trie)
    dsa_engine.load_books(books, db=db)

    print(f"[DSA ENGINE] Loaded {len(books)} books into AVL, HashTable, and Trie.")
    return dsa_engine
