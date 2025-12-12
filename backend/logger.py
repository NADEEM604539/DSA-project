"""
logger.py

Role: Centralized logger for all DSA operations and core backend actions.
Used to track AVL rotations, Hash collisions, Trie inserts, searches, and CRUD operations.
Logs are persisted to the `system_logs` table in the database.
"""

from sqlalchemy.orm import Session
from datetime import datetime
from models import SystemLog
from db import get_db

def log_system(module: str, detail: str, execution_time_ms: float, operation_type: str = "UPDATE"):
    """
    Create a log entry in system_logs.

    Args:
        module (str): Name of the module generating the log (e.g., 'AVL', 'HASH', 'TRIE', 'SERVICE')
        detail (str): Detailed description of the operation
        execution_time_ms (float): Execution time in milliseconds
        operation_type (str): Type of operation (SEARCH, INSERT, DELETE, UPDATE, AVL_ROTATION, HASH_COLLISION, TRIE_INSERT, LOAD, PERFORMANCE)
    """
    db: Session = next(get_db())
    log_entry = SystemLog(
        module=module,
        operation_type=operation_type,
        detail=detail,
        execution_time_ms=execution_time_ms,
        created_at=datetime.now()
    )
    db.add(log_entry)
    db.commit()
