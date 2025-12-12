"""
models.py

Role: SQLAlchemy models representing the high-level library database schema
- Users, roles, permissions
- Books, authors, categories
- Issue records, fines, notifications
- Library policies
- System logs & performance benchmarks
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, Enum, TIMESTAMP, text
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


# ==========================
# ENUM DEFINITIONS
# ==========================
class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    LIBRARIAN = "LIBRARIAN"
    MEMBER = "MEMBER"


class FineType(enum.Enum):
    LATE_RETURN = "LATE_RETURN"
    BOOK_LOST = "BOOK_LOST"


class IssueStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURN_REQUESTED = "RETURN_REQUESTED"
    RETURNED = "RETURNED"


class NotificationType(enum.Enum):
    REMINDER = "REMINDER"
    FINE_NOTICE = "FINE_NOTICE"
    SYSTEM = "SYSTEM"


class DSALogOperation(enum.Enum):
    SEARCH = "SEARCH"
    INSERT = "INSERT"
    DELETE = "DELETE"
    UPDATE = "UPDATE"
    AVL_ROTATION = "AVL_ROTATION"
    HASH_COLLISION = "HASH_COLLISION"
    TRIE_INSERT = "TRIE_INSERT"
    LOAD = "LOAD"
    PERFORMANCE = "PERFORMANCE"


class DSAMethod(enum.Enum):
    HASH_TABLE = "HASH_TABLE"
    AVL_TREE = "AVL_TREE"
    TRIE = "TRIE"
    BINARY_SEARCH = "BINARY_SEARCH"
    LINEAR_SEARCH = "LINEAR_SEARCH"


# ==========================
# 1) USERS
# ==========================
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    issues = relationship("IssueRecord", back_populates="user")
    fines = relationship("UserFine", back_populates="user")


# ==========================
# 2) ROLE PERMISSIONS
# ==========================
class RolePermission(Base):
    __tablename__ = "role_permissions"

    permission_id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(Enum(UserRole), nullable=False)
    permission_key = Column(String(100), nullable=False)
    allowed = Column(Boolean, default=True)


# ==========================
# 3) LIBRARY POLICIES
# ==========================
class LibraryPolicy(Base):
    __tablename__ = "library_policies"

    policy_id = Column(Integer, primary_key=True, default=1)
    max_books_per_user = Column(Integer, default=3, nullable=False)
    max_issue_days = Column(Integer, default=14, nullable=False)
    fine_per_day = Column(Float, default=10.0, nullable=False)
    grace_period_days = Column(Integer, default=0, nullable=False)
    lost_book_penalty_multiplier = Column(Float, default=2.0, nullable=False)
    max_renewals = Column(Integer, default=1)
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))


# ==========================
# 4) AUTHORS
# ==========================
class Author(Base):
    __tablename__ = "authors"

    author_id = Column(Integer, primary_key=True, autoincrement=True)
    author_name = Column(String(255), unique=True, nullable=False)

    books = relationship("Book", back_populates="author")


# ==========================
# 5) CATEGORIES
# ==========================
class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(100), unique=True, nullable=False)

    books = relationship("Book", back_populates="category")


# ==========================
# 6) BOOKS
# ==========================
class Book(Base):
    __tablename__ = "books"

    book_id = Column(Integer, primary_key=True, autoincrement=True)
    isbn = Column(String(20), unique=True, nullable=False)
    title = Column(String(255), nullable=False)

    author_id = Column(Integer, ForeignKey("authors.author_id"))
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    publication_year = Column(Integer)
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)
    added_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    author = relationship("Author", back_populates="books")
    category = relationship("Category", back_populates="books")
    issues = relationship("IssueRecord", back_populates="book", cascade="all, delete-orphan")


# ==========================
# 7) ISSUE RECORDS
# ==========================
class IssueRecord(Base):
    __tablename__ = "issue_records"

    issue_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.book_id"), nullable=False)

    issued_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    due_date = Column(TIMESTAMP, nullable=False)
    returned_at = Column(TIMESTAMP, nullable=True)
    
    status = Column(Enum(IssueStatus), default=IssueStatus.PENDING, nullable=False)

    is_lost = Column(Boolean, default=False)
    is_renewed = Column(Integer, default=0)
    renewal_count = Column(Integer, default=0)
    late_days = Column(Integer, default=0)
    fine_amount = Column(Float, default=0)

    user = relationship("User", back_populates="issues")
    book = relationship("Book", back_populates="issues")
    fines = relationship("UserFine", back_populates="issue")


# ==========================
# 8) USER FINES
# ==========================
class UserFine(Base):
    __tablename__ = "user_fines"

    fine_id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(Integer, ForeignKey("issue_records.issue_id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    fine_type = Column(Enum(FineType), nullable=False)
    fine_amount = Column(Float, nullable=False)
    is_paid = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    paid_at = Column(TIMESTAMP, nullable=True)

    issue = relationship("IssueRecord", back_populates="fines")
    user = relationship("User", back_populates="fines")


# ==========================
# 9) NOTIFICATIONS (Announcements - Broadcast to all users)
# ==========================
class Notification(Base):
    __tablename__ = "announcements"

    announcement_id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String(500), nullable=False)
    announcement_type = Column(Enum(NotificationType), default=NotificationType.SYSTEM)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


# ==========================
# 10) SYSTEM LOGS
# ==========================
class SystemLog(Base):
    __tablename__ = "system_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    module = Column(String(100), nullable=False)
    operation_type = Column(Enum(DSALogOperation), nullable=False)
    detail = Column(String(1000))
    execution_time_ms = Column(Float)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


# ==========================
# 11) PERFORMANCE BENCHMARKS
# ==========================
class PerformanceBenchmark(Base):
    __tablename__ = "performance_benchmarks"

    benchmark_id = Column(Integer, primary_key=True, autoincrement=True)
    operation = Column(String(100), nullable=False)
    dsa_method = Column(String(50), nullable=False)
    execution_time_ms = Column(Float, nullable=False)
    result_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
