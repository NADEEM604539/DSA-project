"""
schemas.py

Role: Pydantic models for request validation and response serialization.
- Separate schemas for Admin, Librarian, Member actions
- Ensures clean data flow between frontend and backend
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==========================
# ENUMS
# ==========================
class UserRole(str, Enum):
    ADMIN = "ADMIN"
    LIBRARIAN = "LIBRARIAN"
    MEMBER = "MEMBER"


class FineType(str, Enum):
    LATE_RETURN = "LATE_RETURN"
    BOOK_LOST = "BOOK_LOST"


class NotificationType(str, Enum):
    REMINDER = "REMINDER"
    FINE_NOTICE = "FINE_NOTICE"
    SYSTEM = "SYSTEM"


# ==========================
# USER SCHEMAS
# ==========================
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    role: UserRole = UserRole.MEMBER


class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    class Config:
        orm_mode = True


# ==========================
# AUTHOR & CATEGORY
# ==========================
class AuthorCreate(BaseModel):
    author_name: str


class AuthorResponse(BaseModel):
    author_id: int
    author_name: str

    class Config:
        orm_mode = True


class CategoryCreate(BaseModel):
    category_name: str


class CategoryResponse(BaseModel):
    category_id: int
    category_name: str

    class Config:
        orm_mode = True


# ==========================
# BOOK SCHEMAS
# ==========================
class BookCreate(BaseModel):
    isbn: str
    title: str
    author_id: int
    category_id: int
    publication_year: Optional[int] = None
    total_copies: int = 1


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author_id: Optional[int] = None
    category_id: Optional[int] = None
    publication_year: Optional[int] = None
    total_copies: Optional[int] = None
    
    class Config:
        extra = "allow"


class BookResponse(BaseModel):
    book_id: int
    isbn: str
    title: str
    author: AuthorResponse
    category: CategoryResponse
    publication_year: Optional[int]
    total_copies: int
    available_copies: int
    added_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ==========================
# ISSUE RECORDS
# ==========================
class IssueCreate(BaseModel):
    user_id: int
    book_id: int


class IssueResponse(BaseModel):
    issue_id: int
    user_id: int
    book_id: int
    issued_at: datetime
    due_date: datetime
    returned_at: Optional[datetime]
    is_lost: bool
    is_renewed: int
    late_days: int
    fine_amount: float

    class Config:
        orm_mode = True


# ==========================
# FINES
# ==========================
class FineResponse(BaseModel):
    fine_id: int
    issue_id: int
    user_id: int
    fine_type: FineType
    amount: float
    is_paid: bool
    created_at: datetime
    paid_at: Optional[datetime]

    class Config:
        orm_mode = True


# ==========================
# NOTIFICATIONS
# ==========================
class NotificationCreate(BaseModel):
    user_id: int
    message: str
    type: NotificationType = NotificationType.SYSTEM


class NotificationResponse(BaseModel):
    notification_id: int
    user_id: int
    message: str
    type: NotificationType
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True


# ==========================
# LIBRARY POLICY
# ==========================
class LibraryPolicyUpdate(BaseModel):
    max_books_per_user: Optional[int] = None
    max_issue_days: Optional[int] = None
    fine_per_day: Optional[float] = None
    grace_period_days: Optional[int] = None
    lost_book_penalty_multiplier: Optional[float] = None
    max_renewals: Optional[int] = None
    
    class Config:
        extra = "allow"


class LibraryPolicyResponse(BaseModel):
    policy_id: int
    max_books_per_user: int
    max_issue_days: int
    fine_per_day: float
    grace_period_days: int
    lost_book_penalty_multiplier: float
    max_renewals: int
    updated_at: datetime

    class Config:
        orm_mode = True


# ==========================
# ADMIN OPERATIONS
# ==========================
class BookOverrideRequest(BaseModel):
    total_copies: Optional[int] = None
    available_copies: Optional[int] = None
    
    class Config:
        extra = "allow"

