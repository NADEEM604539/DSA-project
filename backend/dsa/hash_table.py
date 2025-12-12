"""
dsa/hash_table.py

Role: Hash Table implementation keyed by ISBN for O(1) book lookup.
- Supports insert, search, and delete operations.
- Uses chaining (lists) to handle collisions.
- Logs collisions for performance demonstration.
- Ideal for showing hash table behavior in presentations.
"""

from typing import List, Optional
from models import Book
from logger import log_system
from sqlalchemy.orm import Session
import time


class HashTable:
    """Hash Table using chaining to store books by ISBN"""

    def __init__(self, size: int = 1024):
        """
        Initialize hash table
        :param size: Number of buckets
        """
        self.size = size
        self.buckets: List[List[Book]] = [[] for _ in range(size)]

    def _hash(self, key: str) -> int:
        """Compute simple hash of ISBN"""
        return sum(ord(c) for c in key) % self.size

    # ---------------------------
    # Public interface
    # ---------------------------
    def insert(self, key: str, book: Book, db: Optional[Session] = None):
        """
        Insert a book into the hash table
        :param key: ISBN
        :param book: Book object
        """
        index = self._hash(key)
        bucket = self.buckets[index]

        # Check for duplicates
        for i, b in enumerate(bucket):
            if b.isbn == key:
                bucket[i] = book
                return

        # Collision detected if bucket not empty
        if bucket:
            print(f"[HASH_COLLISION] ISBN: {key} collided at index {index}")
            if db:
                log_system(module="HASH_TABLE", operation_type="HASH_COLLISION",
                           detail=f"Collision for ISBN {key} at index {index}",
                           execution_time_ms=0)

        bucket.append(book)

    def get(self, key: str) -> Optional[Book]:
        """
        Retrieve a book by ISBN
        :param key: ISBN
        :return: Book object or None
        """
        index = self._hash(key)
        bucket = self.buckets[index]
        for b in bucket:
            if b.isbn == key:
                return b
        return None

    def delete(self, key: str, db: Optional[Session] = None):
        """
        Delete a book from hash table
        :param key: ISBN
        """
        index = self._hash(key)
        bucket = self.buckets[index]
        for i, b in enumerate(bucket):
            if b.isbn == key:
                del bucket[i]
                return
        # If deletion failed
        if db:
            log_system(module="HASH_TABLE", operation_type="DELETE",
                       detail=f"Failed deletion for ISBN {key}", execution_time_ms=0)

    def update(self, key: str, book: Book):
        """Update a book in hash table (same as insert)"""
        self.insert(key, book)
