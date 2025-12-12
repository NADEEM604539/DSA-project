"""
dsa/trie.py

Role: Trie (Prefix Tree) for fast title/author autocomplete.
- Supports insert, prefix search, and deletion.
- Ideal for showing string search efficiency in presentations.
- Logs insertion operations to system logs.
"""

from typing import Dict, List, Optional
from models import Book
from logger import log_system
from sqlalchemy.orm import Session
import time


class TrieNode:
    """Node of a Trie"""
    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.is_end_of_word: bool = False
        self.books: List[Book] = []  # Books that match this node (for prefix search)


class Trie:
    """Trie implementation for book titles/authors"""
    def __init__(self):
        self.root = TrieNode()

    # ---------------------------
    # Public interface
    # ---------------------------
    def insert(self, word: str, book: Book, db: Optional[Session] = None):
        """
        Insert a word (title or author) into the trie
        :param word: title/author string
        :param book: Book object
        """
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.books.append(book)

        # Log insertion
        if db:
            log_system(module="TRIE", operation_type="TRIE_INSERT",
                       detail=f"Inserted word '{word}'", execution_time_ms=0)

    def prefix_search(self, prefix: str) -> List[Book]:
        """
        Search for books with given prefix
        :param prefix: Prefix string
        :return: List of matching Book objects
        """
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]

        # Collect all books under this node
        result: List[Book] = []
        self._collect(node, result)
        return result

    def delete(self, word: str, book: Book) -> bool:
        """
        Delete a specific book from trie (if present)
        :param word: title/author string
        :param book: Book object
        :return: True if deleted, False if not found
        """
        return self._delete(self.root, word.lower(), 0, book)

    # ---------------------------
    # Internal helpers
    # ---------------------------
    def _collect(self, node: TrieNode, result: List[Book]):
        """Recursively collect all books under a node"""
        if node.is_end_of_word:
            result.extend(node.books)
        for child in node.children.values():
            self._collect(child, result)

    def _delete(self, node: TrieNode, word: str, index: int, book: Book) -> bool:
        """Recursively delete a book from trie"""
        if index == len(word):
            if node.is_end_of_word and book in node.books:
                node.books.remove(book)
                if not node.books:
                    node.is_end_of_word = False
                return True
            return False
        char = word[index]
        if char in node.children:
            deleted = self._delete(node.children[char], word, index + 1, book)
            # Clean up empty child nodes
            if deleted and not node.children[char].children and not node.children[char].is_end_of_word:
                del node.children[char]
            return deleted
        return False
