"""
core/engine.py

Role: Central DSA Engine that manages all in-memory data structures:
- AVL Tree: for sorted book traversal (title/author)
- Hash Table: for O(1) ISBN lookups
- Trie: for prefix search on titles/authors

Responsibilities:
- Load data from database into DSA structures
- Provide unified search interface for services
- Ensure fast, DSA-first lookups before touching DB
"""

from typing import List, Optional
from dsa.avl import AVLTree
from dsa.hash_table import HashTable
from dsa.trie import Trie
from models import Book
from sqlalchemy.orm import Session


class DSAEngine:
    """DSA Manager combining AVL, HashTable, Trie"""
    def __init__(self, dataset_size: int = 1000, max_depth: int = 20):
        """
        Initialize DSA Engine with configurable parameters.
        :param dataset_size: Expected size of dataset for optimization
        :param max_depth: Maximum depth for tree structures
        """
        self.dataset_size = dataset_size
        self.max_depth = max_depth
        # Sorted tree for alphabetical listing
        self.avl = AVLTree()
        # Hash table for ISBN-based O(1) lookup
        self.hash_table = HashTable()
        # Trie for prefix-based search
        self.trie = Trie()

    # ---------------------------
    # Load from DB
    # ---------------------------
    def load_books(self, books: List[Book], db: Optional[Session] = None):
        """
        Populate all DSA structures with books
        :param books: list of Book objects from DB
        """
        for book in books:
            # AVL insertion (for sorted traversal)
            self.avl.insert(book.title.lower(), book)

            # Hash table insertion (for O(1) ISBN lookup)
            self.hash_table.insert(book.isbn, book, db=db)

            # Trie insertion (for prefix search)
            self.trie.insert(book.title, book, db=db)

    # ---------------------------
    # Search operations
    # ---------------------------
    def search_by_isbn(self, isbn: str) -> Optional[Book]:
        """Search book via Hash Table (O(1))"""
        return self.hash_table.get(isbn)

    def search_by_title(self, title: str) -> Optional[Book]:
        """Exact match using AVL Tree"""
        return self.avl.search(title.lower())

    def search_by_prefix(self, prefix: str) -> List[Book]:
        """Prefix search using Trie"""
        return self.trie.prefix_search(prefix)

    def get_all_sorted(self) -> List[Book]:
        """Return all books sorted by title using AVL inorder traversal"""
        return self.avl.inorder_traversal()
