"""
services/library.py

Role: Core backend service coordinating DSA structures (AVL, Hash, Trie) with database operations.
- All book search, issue, return, and lost operations pass through this layer.
- Ensures DSA-first operations; DB is updated to stay in sync.
- Handles fines, renewals, and policy enforcement.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dsa.avl import AVLTree
from dsa.hash_table import HashTable
from dsa.trie import Trie
from db import get_db
from models import Book, IssueRecord, User, LibraryPolicy, UserFine
from logger import log_system
from utils import calculate_fine, compute_due_date, compute_lost_penalty

# ---------------------------
# Global DSA structures (in-memory)
# ---------------------------
avl_titles = AVLTree()          # AVL for sorted title operations
hash_isbn = HashTable()          # Hash for O(1) lookup by ISBN
trie_titles = Trie()             # Trie for prefix searches

# ---------------------------
# Load books from DB → Build DSA
# ---------------------------
def load_from_db(db: Session):
    """
    Load all books from DB into DSA structures at startup.
    """
    books = db.query(Book).all()
    for book in books:
        avl_titles.insert(book.title, book.book_id)
        hash_isbn.insert(book.isbn, book.book_id)
        trie_titles.insert(book.title, book, db)  # Pass book object, not book_id

    log_system("LOAD", f"Loaded {len(books)} books into DSA structures", 0)


# ---------------------------
# Add / Remove / Update Books
# ---------------------------
def add_new_book(db: Session, book: Book):
    db.add(book)
    db.commit()
    db.refresh(book)

    # DSA sync
    avl_titles.insert(book.title, book.book_id)
    hash_isbn.insert(book.isbn, book.book_id)
    trie_titles.insert(book.title, book, db)  # Pass book object to trie, not book_id

    log_system("INSERT", f"Book '{book.title}' added to DSA + DB", 0)


def remove_book(db: Session, book: Book):
    # DSA sync
    avl_titles.delete(book.title)
    hash_isbn.delete(book.isbn)
    trie_titles.delete(book.title, book)  # Pass book object to delete method

    db.delete(book)
    db.commit()
    log_system("DELETE", f"Book '{book.title}' removed from DSA + DB", 0)


def update_existing_book(db: Session, book: Book, updated_fields: dict):
    # Update DB
    for key, value in updated_fields.items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    log_system("UPDATE", f"Book '{book.title}' updated", 0)

    # Optional: Rebuild DSA if title or ISBN changed
    if "title" in updated_fields or "isbn" in updated_fields:
        remove_book(db, book)
        add_new_book(db, book)


# ---------------------------
# DSA Search Functions
# ---------------------------
def search_by_title(db: Session, title_prefix: str):
    """
    Use Trie → AVL → Hash sequence for searching titles
    """
    matched_ids = trie_titles.prefix_search(title_prefix)
    results = []
    for book_id in matched_ids:
        book = db.query(Book).filter_by(book_id=book_id).first()
        if book:
            results.append(book)
    return results


def search_by_author(db: Session, author_prefix: str):
    """
    Use Trie on author names → AVL for sorting
    """
    # Simple example: filter authors starting with prefix
    from models import Author
    authors = db.query(Author).filter(Author.author_name.like(f"{author_prefix}%")).all()
    results = []
    for author in authors:
        books = db.query(Book).filter_by(author_id=author.author_id).all()
        results.extend(books)
    return results


def search_by_isbn(db: Session, isbn: str):
    """
    Hash table exact ISBN lookup using DSA Engine
    """
    from core.loader import dsa_engine
    book = dsa_engine.search_by_isbn(isbn)
    if not book:
        return None
    return book


# ---------------------------
# Issue / Return / Lost Operations
# ---------------------------
def issue_book(db: Session, user: User, book: Book):
    """
    Issue book to member respecting max books per user.
    Calculates due date.
    Sets initial status to PENDING (needs librarian approval).
    """
    from models import IssueStatus
    
    policy = db.query(LibraryPolicy).first()
    active_issues = db.query(IssueRecord).filter(
        IssueRecord.user_id == user.user_id,
        IssueRecord.status.in_([IssueStatus.PENDING, IssueStatus.APPROVED])
    ).count()
    if active_issues >= policy.max_books_per_user:
        raise Exception(f"Max books per user ({policy.max_books_per_user}) reached")

    due_date = compute_due_date(datetime.now(), policy.max_issue_days)
    issue = IssueRecord(
        user_id=user.user_id, 
        book_id=book.book_id, 
        due_date=due_date,
        status=IssueStatus.PENDING
    )
    db.add(issue)
    book.available_copies -= 1
    db.commit()
    db.refresh(issue)
    log_system("INSERT", f"Book '{book.title}' issued to {user.full_name}", 0)
    return issue


def return_book(db: Session, issue: IssueRecord):
    """
    Return a book and calculate fines if overdue.
    Sets status to RETURNED.
    """
    from models import IssueStatus, UserFine, FineType
    
    issue.returned_at = datetime.now()
    issue.status = IssueStatus.RETURNED
    policy = db.query(LibraryPolicy).first()
    late_days = max(0, (issue.returned_at - issue.due_date).days - policy.grace_period_days)
    fine_amount = calculate_fine(late_days, policy.fine_per_day)
    issue.late_days = late_days
    issue.fine_amount = fine_amount

    # Update book availability
    book = db.query(Book).filter_by(book_id=issue.book_id).first()
    if book:
        book.available_copies += 1
    
    db.add(issue)  # Ensure the issue is added to session
    db.commit()
    db.refresh(issue)  # Refresh to get updated values
    
    # Create fine record if there's a late fee
    if fine_amount > 0:
        user_fine = UserFine(
            issue_id=issue.issue_id,
            user_id=issue.user_id,
            fine_type=FineType.LATE_RETURN,
            fine_amount=fine_amount,
            is_paid=False
        )
        db.add(user_fine)
        db.commit()
        log_system("INSERT", f"Late return fine of {fine_amount} created for user {issue.user_id}", 0)
    
    log_system("UPDATE", f"Book '{book.title if book else 'Unknown'}' returned by {issue.user_id}", 0)
    return issue


def mark_lost(db: Session, issue: IssueRecord):
    """
    Mark a book as lost and calculate penalty
    """
    issue.is_lost = True
    policy = db.query(LibraryPolicy).first()
    lost_penalty = compute_lost_penalty(issue, policy)
    issue.fine_amount = lost_penalty

    # Update book availability
    book = db.query(Book).filter_by(book_id=issue.book_id).first()
    book.available_copies -= 1
    db.commit()
    log_system("UPDATE", f"Book '{book.title}' marked lost by {issue.user_id}", 0)
    return issue


# ---------------------------
# Renewal Operations
# ---------------------------
def renew_book(db: Session, issue: IssueRecord):
    """
    Renew a borrowed book.
    Extends due date by max_issue_days and increments renewal count.
    """
    policy = db.query(LibraryPolicy).first()
    
    if issue.renewal_count >= policy.max_renewals:
        raise Exception("Maximum renewals exceeded")
    
    # Calculate new due date
    new_due_date = issue.due_date + timedelta(days=policy.max_issue_days)
    issue.due_date = new_due_date
    issue.renewal_count += 1
    
    db.commit()
    log_system("UPDATE", f"Issue {issue.issue_id} renewed by {issue.user_id}", 0)
    return issue


# ---------------------------
# Fine Management
# ---------------------------
def collect_fine(db: Session, fine_id: int):
    """
    Mark a fine as paid.
    """
    fine = db.query(UserFine).filter_by(fine_id=fine_id).first()
    if not fine:
        raise Exception("Fine not found")
    
    fine.is_paid = True
    fine.paid_at = datetime.now()
    db.commit()
    log_system("UPDATE", f"Fine {fine_id} collected for user {fine.user_id}", 0)
    return fine


def create_fine(db: Session, user_id: int, fine_amount: float, fine_type: str):
    """
    Create a new fine record for a user.
    """
    fine = UserFine(
        user_id=user_id,
        fine_amount=fine_amount,
        fine_type=fine_type,
        is_paid=False
    )
    db.add(fine)
    db.commit()
    db.refresh(fine)
    log_system("INSERT", f"Fine {fine.fine_id} created for user {user_id}", 0)
    return fine


def get_user_fines(db: Session, user_id: int):
    """
    Get all fines for a user.
    """
    fines = db.query(UserFine).filter_by(user_id=user_id).all()
    return fines


def get_unpaid_fines(db: Session, user_id: int):
    """
    Get unpaid fines for a user.
    """
    fines = db.query(UserFine).filter(
        UserFine.user_id == user_id,
        UserFine.is_paid == False
    ).all()
    return fines


# ---------------------------
# Notification Management
# ---------------------------
def send_notification(db: Session, user_id: int, message: str, notification_type: str):
    """
    Send a notification to a user.
    """
    from models import Notification, NotificationType
    
    notification = Notification(
        user_id=user_id,
        message=message,
        notification_type=NotificationType[notification_type]
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    log_system("INSERT", f"Notification sent to {user_id}: {message[:50]}", 0)
    return notification


def send_reminder(db: Session, user_id: int, book_title: str, due_date: datetime):
    """
    Send a reminder notification for an upcoming due date.
    """
    message = f"Reminder: '{book_title}' is due on {due_date.strftime('%Y-%m-%d')}"
    return send_notification(db, user_id, message, "REMINDER")


def send_fine_notice(db: Session, user_id: int, fine_amount: float):
    """
    Send a fine notice to a user.
    """
    message = f"Fine notice: You have an outstanding fine of {fine_amount} units"
    return send_notification(db, user_id, message, "FINE_NOTICE")


def get_user_notifications(db: Session, user_id: int):
    """
    Get all notifications for a user.
    """
    from models import Notification
    
    notifications = db.query(Notification).filter_by(user_id=user_id).order_by(
        Notification.created_at.desc()
    ).all()
    return notifications


# ---------------------------
# Issue History & Statistics
# ---------------------------
def get_user_issue_history(db: Session, user_id: int):
    """
    Get complete issue history for a user.
    """
    issues = db.query(IssueRecord).filter_by(user_id=user_id).all()
    return issues


def get_user_active_issues(db: Session, user_id: int):
    """
    Get current (unreturned) issues for a user.
    """
    issues = db.query(IssueRecord).filter(
        IssueRecord.user_id == user_id,
        IssueRecord.returned_at == None
    ).all()
    return issues


def get_overdue_issues(db: Session):
    """
    Get all overdue issues across the library.
    """
    issues = db.query(IssueRecord).filter(
        IssueRecord.returned_at == None,
        IssueRecord.due_date < datetime.now()
    ).all()
    return issues


# ---------------------------
# DSA Performance Logging
# ---------------------------
def log_search_performance(db: Session, dsa_method: str, query_time_ms: float, result_count: int):
    """
    Log performance metrics for search operations.
    """
    from models import PerformanceBenchmark
    
    benchmark = PerformanceBenchmark(
        operation="SEARCH",
        dsa_method=dsa_method,
        execution_time_ms=query_time_ms,
        result_count=result_count
    )
    db.add(benchmark)
    db.commit()
    log_system("PERFORMANCE", f"{dsa_method} search: {query_time_ms}ms, {result_count} results", 0)
