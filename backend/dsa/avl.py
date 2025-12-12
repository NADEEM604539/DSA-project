"""
dsa/avl.py

Role: Balanced AVL Tree implementation for storing books in sorted order (by title).
- Supports insert, delete, search, and in-order traversal.
- Logs AVL rotations to system logs via logger for performance & demonstration.
- Ideal for explaining self-balancing trees in presentations.
"""

from typing import Optional, List
from models import Book
from logger import log_system
from sqlalchemy.orm import Session
import time


class AVLNode:
    """Node of an AVL Tree"""
    def __init__(self, key: str, value: Book):
        self.key = key          # Key used for sorting (e.g., book.title)
        self.value = value      # Associated book object
        self.left = None        # Left child
        self.right = None       # Right child
        self.height = 1         # Node height for balancing


class AVLTree:
    """AVL Tree for sorted book storage"""
    def __init__(self):
        self.root: Optional[AVLNode] = None

    # ---------------------------
    # Public interface
    # ---------------------------
    def insert(self, key: str, value: Book):
        """Insert a key-value pair into the AVL tree"""
        self.root = self._insert(self.root, key, value)

    def delete(self, key: str):
        """Delete a key from the AVL tree"""
        self.root = self._delete(self.root, key)

    def search(self, key: str) -> Optional[Book]:
        """Search for a key in the AVL tree"""
        node = self._search(self.root, key)
        return node.value if node else None

    def inorder_traversal(self) -> List[Book]:
        """Return books in sorted order (in-order traversal)"""
        result = []
        self._inorder(self.root, result)
        return result

    # ---------------------------
    # Internal helper methods
    # ---------------------------
    def _height(self, node: Optional[AVLNode]) -> int:
        return node.height if node else 0

    def _get_balance(self, node: Optional[AVLNode]) -> int:
        if not node:
            return 0
        return self._height(node.left) - self._height(node.right)

    def _right_rotate(self, y: AVLNode) -> AVLNode:
        x = y.left
        T2 = x.right

        # Perform rotation
        x.right = y
        y.left = T2

        # Update heights
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        x.height = 1 + max(self._height(x.left), self._height(x.right))

        # Log rotation
        print(f"[AVL_ROTATION] Right rotation on node: {y.key}")
        return x

    def _left_rotate(self, x: AVLNode) -> AVLNode:
        y = x.right
        T2 = y.left

        # Perform rotation
        y.left = x
        x.right = T2

        # Update heights
        x.height = 1 + max(self._height(x.left), self._height(x.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))

        # Log rotation
        print(f"[AVL_ROTATION] Left rotation on node: {x.key}")
        return y

    # ---------------------------
    # Recursive insert/delete
    # ---------------------------
    def _insert(self, node: Optional[AVLNode], key: str, value: Book) -> AVLNode:
        # Step 1: Perform normal BST insert
        if not node:
            return AVLNode(key, value)

        if key < node.key:
            node.left = self._insert(node.left, key, value)
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
        else:
            # Duplicate keys not allowed, update value
            node.value = value
            return node

        # Step 2: Update height
        node.height = 1 + max(self._height(node.left), self._height(node.right))

        # Step 3: Check balance
        balance = self._get_balance(node)

        # Step 4: Rotate if unbalanced

        # Left Left Case
        if balance > 1 and key < node.left.key:
            return self._right_rotate(node)

        # Right Right Case
        if balance < -1 and key > node.right.key:
            return self._left_rotate(node)

        # Left Right Case
        if balance > 1 and key > node.left.key:
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)

        # Right Left Case
        if balance < -1 and key < node.right.key:
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)

        return node

    def _min_value_node(self, node: AVLNode) -> AVLNode:
        """Get node with minimum key in subtree"""
        current = node
        while current.left:
            current = current.left
        return current

    def _delete(self, node: Optional[AVLNode], key: str) -> Optional[AVLNode]:
        # Step 1: Perform standard BST delete
        if not node:
            return node

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            # Node with only one child or no child
            if not node.left:
                return node.right
            elif not node.right:
                return node.left

            # Node with two children: get inorder successor
            temp = self._min_value_node(node.right)
            node.key = temp.key
            node.value = temp.value
            node.right = self._delete(node.right, temp.key)

        # Step 2: Update height
        node.height = 1 + max(self._height(node.left), self._height(node.right))

        # Step 3: Check balance
        balance = self._get_balance(node)

        # Step 4: Rotate if unbalanced
        # Left Left
        if balance > 1 and self._get_balance(node.left) >= 0:
            return self._right_rotate(node)
        # Left Right
        if balance > 1 and self._get_balance(node.left) < 0:
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)
        # Right Right
        if balance < -1 and self._get_balance(node.right) <= 0:
            return self._left_rotate(node)
        # Right Left
        if balance < -1 and self._get_balance(node.right) > 0:
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)

        return node

    def _search(self, node: Optional[AVLNode], key: str) -> Optional[AVLNode]:
        """Recursive search for key"""
        if not node or node.key == key:
            return node
        if key < node.key:
            return self._search(node.left, key)
        else:
            return self._search(node.right, key)

    def _inorder(self, node: Optional[AVLNode], result: List[Book]):
        """Recursive in-order traversal"""
        if not node:
            return
        self._inorder(node.left, result)
        result.append(node.value)
        self._inorder(node.right, result)
