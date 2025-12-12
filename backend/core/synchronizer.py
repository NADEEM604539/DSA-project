"""
core/synchronizer.py

Role: Synchronizer module to ensure DSA structures (AVL, HashTable, Trie)
stay consistent with database operations.

Responsibilities:
- When a book is added, deleted, or updated, update both DB and DSA.
- Maintains atomicity between in-memory and persistent storage.
- Keeps DSA-first approach intact.
"""

from sqlalchemy.orm import Session
from models import Book
from core.loader import dsa_engine


def add_book(db: Session, book: Book):
    """
    Add a new book to the database and DSA structures
    :param db: SQLAlchemy session
    :param book: Book object to add
    """
    db.add(book)
    db.commit()
    db.refresh(book)

    # Update DSA structures
    dsa_engine.avl.insert(book.title.lower(), book, db=db)
    dsa_engine.hash_table.insert(book.isbn, book, db=db)
    dsa_engine.trie.insert(book.title, book, db=db)


def delete_book(db: Session, book: Book):
    """
    Delete a book from database and DSA structures
    :param db: SQLAlchemy session
    :param book: Book object to delete
    """
    # Remove from DSA structures first
    dsa_engine.avl.delete(book.title.lower())
    dsa_engine.hash_table.delete(book.isbn)
    dsa_engine.trie.delete(book.title, book)

    # Remove from DB
    db.delete(book)
    db.commit()


def update_book(db: Session, book: Book, updated_fields: dict):
    """
    Update book fields in DB and refresh DSA structures
    :param db: SQLAlchemy session
    :param book: Book object to update
    :param updated_fields: dict of fields to update
    """
    # Delete old entries in DSA first
    dsa_engine.avl.delete(book.title.lower())
    dsa_engine.hash_table.delete(book.isbn)
    dsa_engine.trie.delete(book.title, book)

    # Update DB fields
    for key, value in updated_fields.items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)

    # Re-insert updated book into DSA
    dsa_engine.avl.insert(book.title.lower(), book, db=db)
    dsa_engine.hash_table.insert(book.isbn, book, db=db)
    dsa_engine.trie.insert(book.title, book, db=db)
