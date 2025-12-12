"""
routes/admin.py

Role: Admin-only endpoints for managing the library.
- Backend is API-first: Frontend (with Clerk) sends API requests
- Can update library policies, add/remove books, view system logs
- Uses services/library.py for all DSA-first operations

User creation flow:
1. Frontend authenticates user with Clerk
2. Frontend calls POST /admin/users with Clerk user_id and details
3. Backend stores user in database
4. Returns user_id for subsequent API calls
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import Book, LibraryPolicy, SystemLog, IssueRecord, UserFine, User
from schemas import BookCreate, BookUpdate, LibraryPolicyUpdate, BookOverrideRequest
from services.library import add_new_book, remove_book, update_existing_book
from datetime import datetime, timedelta
from auth import get_current_user
from sqlalchemy import func

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

# ---------------------------
# Dashboard Stats
# ---------------------------
@router.get("/stats")
def admin_get_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics for admin overview
    """
    try:
        # Total books
        total_books = db.query(func.count(Book.book_id)).scalar() or 0
        
        # Total members
        total_members = db.query(func.count(User.user_id)).filter(User.role == 'MEMBER').scalar() or 0
        
        # Active issues (issued but not returned)
        active_issues = db.query(func.count(IssueRecord.issue_id)).filter(
            IssueRecord.status.in_(['PENDING', 'APPROVED'])
        ).scalar() or 0
        
        # Overdue books (due_date passed and not returned)
        today = datetime.now().date()
        overdue_books = db.query(func.count(IssueRecord.issue_id)).filter(
            IssueRecord.status.in_(['PENDING', 'APPROVED']),
            IssueRecord.due_date < today
        ).scalar() or 0
        
        # Unpaid fines
        unpaid_fines = db.query(UserFine).filter(UserFine.is_paid == False).all()
        unpaid_fines_count = len(unpaid_fines)
        unpaid_fines_amount = sum([f.fine_amount for f in unpaid_fines])
        
        return {
            "total_books": total_books,
            "total_members": total_members,
            "active_issues": active_issues,
            "overdue_books": overdue_books,
            "unpaid_fines_count": unpaid_fines_count,
            "unpaid_fines_amount": float(unpaid_fines_amount)
        }
    except Exception as e:
        print(f"Error in admin_get_stats: {str(e)}")
        return {
            "total_books": 0,
            "total_members": 0,
            "active_issues": 0,
            "overdue_books": 0,
            "unpaid_fines_count": 0,
            "unpaid_fines_amount": 0
        }


# ---------------------------
# Recent Activities
# ---------------------------
@router.get("/activities")
def admin_get_activities(db: Session = Depends(get_db)):
    """
    Get recent system activities
    """
    try:
        # Get recent system logs
        logs = db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(20).all()
        
        activities = []
        for log in logs:
            activities.append({
                "action": log.operation_type,
                "description": log.detail,
                "created_at": log.created_at.isoformat() if log.created_at else None
            })
        
        return {"activities": activities}
    except Exception as e:
        print(f"Error in admin_get_activities: {str(e)}")
        return {"activities": []}


# ---------------------------
# Book Management
# ---------------------------
@router.post("/books")
def admin_add_book(book_data: BookCreate, db: Session = Depends(get_db)):
    """
    Add a new book to the system
    """
    try:
        book = Book(**book_data.model_dump())
        add_new_book(db, book)
        return {"message": "Book added successfully", "book_id": book.book_id}
    except Exception as e:
        db.rollback()
        if "Duplicate entry" in str(e) and "isbn" in str(e):
            raise HTTPException(status_code=400, detail="ISBN already exists")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/books/{book_id}")
def admin_delete_book(book_id: int, db: Session = Depends(get_db)):
    """
    Delete a book from the system
    """
    book = db.query(Book).filter_by(book_id=book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    remove_book(db, book)
    return {"message": "Book deleted successfully"}


@router.put("/books/{book_id}")
def admin_update_book(book_id: int, book_update: BookUpdate, db: Session = Depends(get_db)):
    """
    Update book details
    """
    from schemas import BookUpdate
    
    book = db.query(Book).filter_by(book_id=book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Update only provided fields
    update_data = book_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(book, key, value)
    
    db.commit()
    db.refresh(book)
    return {"message": "Book updated successfully", "book_id": book.book_id}


# ---------------------------
# Library Policy Management
# ---------------------------
@router.put("/policies")
def admin_update_policy(policy_update: LibraryPolicyUpdate, db: Session = Depends(get_db)):
    """
    Update library policies such as max books per user, fine per day, lost penalty multiplier.
    """
    policy = db.query(LibraryPolicy).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    for key, value in policy_update.model_dump(exclude_unset=True).items():
        setattr(policy, key, value)
    db.commit()
    return {"message": "Library policy updated successfully"}


# ---------------------------
# System Logs
# ---------------------------
@router.get("/logs")
def admin_get_logs(db: Session = Depends(get_db)):
    """
    Get all system logs for monitoring DSA operations.
    """
    logs = db.query(SystemLog).order_by(SystemLog.created_at.desc()).all()
    return logs


# ---------------------------
# Get Library Policies
# ---------------------------
@router.get("/policies")
def admin_get_policies(db: Session = Depends(get_db)):
    """
    Get all library policies.
    """
    policy = db.query(LibraryPolicy).first()
    if not policy:
        return {"message": "No policies configured yet"}
    return policy


# ---------------------------
# Get All Users
# ---------------------------
@router.get("/users")
def admin_get_users(db: Session = Depends(get_db)):
    """
    Get all users in the system.
    """
    from models import User
    users = db.query(User).all()
    return {"users": users}


# ---------------------------
# Get All Books
# ---------------------------
@router.get("/books")
def admin_get_books(db: Session = Depends(get_db)):
    """
    Get all books in the system.
    """
    books = db.query(Book).all()
    return {"books": books, "total": len(books)}


# ---------------------------
# Get All Authors
# ---------------------------
@router.get("/authors")
def admin_get_authors(db: Session = Depends(get_db)):
    """
    Get all authors in the system.
    """
    from models import Author
    authors = db.query(Author).all()
    return {"authors": authors, "total": len(authors)}


# ---------------------------
# User Management - CRUD
# ---------------------------
@router.post("/users")
def admin_create_user(
    user_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new user account with JSON body.
    Expected body: {"full_name": "string", "email": "string", "role": "ADMIN|LIBRARIAN|MEMBER"}
    """
    from models import User, UserRole
    
    # Validate required fields
    if "full_name" not in user_data or "email" not in user_data:
        raise HTTPException(status_code=422, detail="full_name and email are required")
    
    full_name = user_data.get("full_name")
    email = user_data.get("email")
    role = user_data.get("role", "MEMBER").upper()
    
    # Check if user already exists
    existing = db.query(User).filter_by(email=email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    try:
        user = User(
            full_name=full_name,
            email=email,
            role=UserRole[role]
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {"message": "User created successfully", "user_id": user.user_id, "email": email}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be ADMIN, LIBRARIAN, or MEMBER")
    except Exception as e:
        db.rollback()
        if "Duplicate entry" in str(e) and "email" in str(e):
            raise HTTPException(status_code=400, detail="Email already exists")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}")
def admin_get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get a specific user's details.
    """
    from models import User
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}


@router.put("/users/{user_id}")
def admin_update_user(
    user_id: int,
    full_name: str = None,
    email: str = None,
    role: str = None,
    db: Session = Depends(get_db)
):
    """
    Update user details.
    """
    from models import User, UserRole
    
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if full_name:
        user.full_name = full_name
    if email:
        user.email = email
    if role:
        user.role = UserRole[role.upper()]
    
    db.commit()
    return {"message": "User updated successfully"}


@router.delete("/users/{user_id}")
def admin_delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user account.
    """
    from models import User
    
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


# ---------------------------
# Role & Permissions Management
# ---------------------------
@router.get("/roles")
def admin_get_roles(db: Session = Depends(get_db)):
    """
    Get all available roles in the system.
    """
    from models import UserRole
    roles = [role.value for role in UserRole]
    return {"roles": roles}


@router.get("/role-permissions")
def admin_get_role_permissions(db: Session = Depends(get_db)):
    """
    Get role-based permissions mapping.
    """
    permissions = {
        "ADMIN": [
            "view_users",
            "manage_users",
            "manage_books",
            "manage_policies",
            "view_logs",
            "manage_categories",
            "view_benchmarks"
        ],
        "LIBRARIAN": [
            "issue_books",
            "return_books",
            "mark_lost",
            "manage_books",
            "collect_fines",
            "send_notifications"
        ],
        "MEMBER": [
            "search_books",
            "view_issues",
            "view_fines",
            "renew_books",
            "view_notifications"
        ]
    }
    return permissions


# ---------------------------
# Category Management - CRUD
# ---------------------------
@router.get("/categories")
def admin_get_categories(db: Session = Depends(get_db)):
    """
    Get all book categories.
    """
    from models import Category
    categories = db.query(Category).all()
    return {"categories": categories}


@router.post("/categories")
def admin_create_category(
    category_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new book category with JSON body.
    Expected body: {"category_name": "string"}
    """
    from models import Category
    
    if "category_name" not in category_data:
        raise HTTPException(status_code=422, detail="category_name is required")
    
    try:
        category = Category(
            category_name=category_data.get("category_name")
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return {"message": "Category created successfully", "category_id": category.category_id}
    except Exception as e:
        db.rollback()
        if "Duplicate entry" in str(e) and "category_name" in str(e):
            raise HTTPException(status_code=400, detail="Category name already exists")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/categories/{category_id}")
def admin_update_category(
    category_id: int,
    category_name: str = None,
    description: str = None,
    db: Session = Depends(get_db)
):
    """
    Update category details.
    """
    from models import Category
    
    category = db.query(Category).filter_by(category_id=category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category_name:
        category.category_name = category_name
    if description:
        category.description = description
    
    db.commit()
    return {"message": "Category updated successfully"}


@router.delete("/categories/{category_id}")
def admin_delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    Delete a category.
    """
    from models import Category
    
    category = db.query(Category).filter_by(category_id=category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(category)
    db.commit()
    
    return {"message": "Category deleted successfully"}


# ---------------------------
# Performance Benchmarks
# ---------------------------
@router.get("/benchmarks")
def admin_get_benchmarks(db: Session = Depends(get_db)):
    """
    Get DSA performance benchmarks.
    """
    from models import PerformanceBenchmark
    try:
        benchmarks = db.query(PerformanceBenchmark).order_by(
            PerformanceBenchmark.created_at.desc()
        ).limit(50).all()
        
        return {
            "benchmarks_count": len(benchmarks),
            "total": len(benchmarks)
        }
    except Exception as e:
        return {
            "benchmarks_count": 0,
            "total": 0
        }


# ---------------------------
# Book Copy Management
# ---------------------------
@router.post("/books/{book_id}/copies")
def admin_override_copies(
    book_id: int,
    total_copies: int,
    available_copies: int,
    db: Session = Depends(get_db)
):
    """
    Override book copy counts (admin override).
    """
    book = db.query(Book).filter_by(book_id=book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book.total_copies = total_copies
    book.available_copies = available_copies
    db.commit()
    
    from logger import log_system
    log_system("UPDATE", f"Book {book_id} copies overridden by admin", book_id)
    
    return {"message": "Book copies updated successfully"}


# ---------------------------
# Mark Book as Lost (Admin Override)
# ---------------------------
@router.post("/books/{book_id}/mark-lost")
def admin_mark_book_lost(
    book_id: int,
    issue_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Mark a book as lost (admin override).
    """
    from models import IssueRecord
    from services.library import mark_lost
    
    book = db.query(Book).filter_by(book_id=book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if issue_id:
        issue = db.query(IssueRecord).filter_by(issue_id=issue_id).first()
        if issue:
            lost_issue = mark_lost(db, issue)
            return {
                "message": "Book marked lost",
                "book_id": book_id,
                "fine_imposed": lost_issue.fine_amount
            }
    
    # Reduce available copies if not linked to specific issue
    book.available_copies = max(0, book.available_copies - 1)
    db.commit()
    
    return {"message": "Book copy marked unavailable"}


# ---------------------------
# System Logs - Extended
# ---------------------------
@router.get("/logs")
def admin_get_logs(limit: int = 100, db: Session = Depends(get_db)):
    """
    Get system logs for monitoring DSA operations.
    """
    logs = db.query(SystemLog).order_by(
        SystemLog.created_at.desc()
    ).limit(limit).all()
    return {"logs": logs, "total": len(logs)}


@router.get("/logs/filter")
def admin_filter_logs(
    operation: str = None,
    dsa_method: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Filter system logs by operation or DSA method.
    """
    query = db.query(SystemLog)
    
    if operation:
        query = query.filter(SystemLog.operation == operation)
    if dsa_method:
        query = query.filter(SystemLog.dsa_method == dsa_method)
    
    logs = query.order_by(SystemLog.created_at.desc()).limit(limit).all()
    return {"logs": logs, "total": len(logs)}


# ---------------------------
# Fines Management
# ---------------------------
@router.get("/fines")
def admin_get_all_fines(db: Session = Depends(get_db)):
    """
    Get all fines (paid and unpaid) across the system.
    """
    from models import UserFine
    fines = db.query(UserFine).all()
    
    paid = sum([f.fine_amount for f in fines if f.is_paid])
    unpaid = sum([f.fine_amount for f in fines if not f.is_paid])
    
    return {
        "fines": fines,
        "summary": {
            "total_fines": paid + unpaid,
            "paid": paid,
            "unpaid": unpaid,
            "count": len(fines)
        }
    }


# ---------------------------
# Announcements Management
# ---------------------------
@router.get("/announcements")
def admin_get_announcements(db: Session = Depends(get_db)):
    """
    Get all announcements (system-wide messages visible to everyone).
    """
    from models import Announcement
    announcements = db.query(Announcement).order_by(
        Announcement.created_at.desc()
    ).all()
    return {"announcements": announcements, "total": len(announcements)}


@router.post("/announcements")
def admin_create_announcement(
    data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new system-wide announcement.
    Message appears to all users (members, librarians, admins).
    """
    from models import Announcement
    
    message = data.get("message", "")
    announcement_type = data.get("announcement_type", "SYSTEM")
    
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    
    announcement = Announcement(
        message=message,
        announcement_type=announcement_type
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    
    from logger import log_system
    log_system("SYSTEM", f"Announcement created: {message}", 0)
    
    return {
        "message": "Announcement created successfully",
        "announcement_id": announcement.announcement_id
    }


@router.delete("/announcements/{announcement_id}")
def admin_delete_announcement(announcement_id: int, db: Session = Depends(get_db)):
    """
    Delete an announcement by ID.
    """
    from models import Announcement
    
    announcement = db.query(Announcement).filter(
        Announcement.announcement_id == announcement_id
    ).first()
    
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    db.delete(announcement)
    db.commit()
    
    from logger import log_system
    log_system("SYSTEM", f"Announcement {announcement_id} deleted", 0)
    
    return {"message": "Announcement deleted successfully"}


@router.put("/books/{book_id}/override", response_model=None)
def override_book_copies(book_id: int, override: BookOverrideRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Override book copy counts (admin only).
    Manually set total_copies and available_copies for a specific book.
    """
    from models import Book
    from logger import log_system
    
    # Check role
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admins can override book counts")
    
    # Find book
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Update book - only if values provided
    old_total = book.total_copies
    old_available = book.available_copies
    
    if override.total_copies is not None:
        if override.total_copies < 0:
            raise HTTPException(status_code=400, detail="Total copies must be non-negative")
        book.total_copies = override.total_copies
    
    if override.available_copies is not None:
        if override.available_copies < 0:
            raise HTTPException(status_code=400, detail="Available copies must be non-negative")
        if override.available_copies > book.total_copies:
            raise HTTPException(status_code=400, detail="Available copies cannot exceed total copies")
        book.available_copies = override.available_copies
    
    db.commit()
    
    # Log operation
    log_system(current_user.user_id, f"Overrode book {book_id} copies from ({old_total}/{old_available}) to ({override.total_copies}/{override.available_copies})", 0)
    
    return {
        "book_id": book.book_id,
        "title": book.title,
        "total_copies": book.total_copies,
        "available_copies": book.available_copies,
        "message": "Book copies updated successfully"
    }


@router.post("/lost/{book_id}", response_model=None)
def mark_book_copies_lost(book_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Mark all active issues of a book as lost (admin only).
    Applies lost book penalty to affected members.
    """
    from models import Book, IssueRecord, User
    from services.library import mark_lost
    from logger import log_system
    
    # Check role
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admins can mark books lost")
    
    # Find book
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Find all unreturned issues for this book
    issues = db.query(IssueRecord).filter(
        IssueRecord.book_id == book_id,
        IssueRecord.returned_at == None
    ).all()
    
    if not issues:
        raise HTTPException(status_code=404, detail="No active issues found for this book")
    
    affected_users = []
    for issue in issues:
        mark_lost(db, issue)
        affected_users.append(issue.user_id)
    
    log_system(current_user.user_id, f"Marked book {book_id} as lost for {len(issues)} active issue(s)", 0)
    
    return {
        "message": f"Marked {len(issues)} issue(s) as lost",
        "book_id": book_id,
        "title": book.title,
        "affected_count": len(issues),
        "affected_user_ids": affected_users
    }


# ---------------------------
# All Issues Management (Admin View)
# ---------------------------
@router.get("/issues")
def admin_get_all_issues(db: Session = Depends(get_db)):
    """
    Get ALL system issues (admin view) - for issue management page
    """
    try:
        issues = db.query(IssueRecord).all()
        return {
            "issues": issues,
            "total": len(issues)
        }
    except Exception as e:
        print(f"Error fetching issues: {str(e)}")
        return {"issues": [], "total": 0}


# ---------------------------
# All Return Requests (Admin View)
# ---------------------------
@router.get("/return-requests")
def admin_get_return_requests(db: Session = Depends(get_db)):
    """
    Get all return requests in the system (admin view)
    """
    try:
        from models import ReturnRequest
        requests = db.query(ReturnRequest).all()
        return {
            "requests": requests,
            "total": len(requests)
        }
    except Exception as e:
        print(f"Error fetching return requests: {str(e)}")
        return {"requests": [], "total": 0}


# ---------------------------
# All Issue Requests (Admin View)
# ---------------------------
@router.get("/issue-requests")
def admin_get_issue_requests(db: Session = Depends(get_db)):
    """
    Get all issue requests in the system (admin view)
    """
    try:
        from models import IssueRequest
        requests = db.query(IssueRequest).all()
        return {
            "requests": requests,
            "total": len(requests)
        }
    except Exception as e:
        print(f"Error fetching issue requests: {str(e)}")
        return {"requests": [], "total": 0}


# ---------------------------
# Send Notification (Announcement)
# ---------------------------
@router.post("/send-notification")
def admin_send_notification(
    message: str,
    notification_type: str = "SYSTEM",
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to broadcast a notification/announcement to all users.
    
    Args:
        message: The notification message
        notification_type: Type of notification (SYSTEM, REMINDER, FINE_NOTICE)
    
    Returns:
        Created notification with ID and timestamp
    """
    try:
        from models import Notification
        from sqlalchemy import Enum as SQLEnum
        
        # Validate notification type
        valid_types = ["SYSTEM", "REMINDER", "FINE_NOTICE"]
        if notification_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid notification_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Create notification
        notification = Notification(
            message=message,
            announcement_type=notification_type
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return {
            "announcement_id": notification.announcement_id,
            "message": notification.message,
            "announcement_type": notification.announcement_type,
            "created_at": notification.created_at.isoformat() if notification.created_at else None,
            "status": "success"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating notification: {str(e)}")


# ---------------------------
# Library Policy Management
# ---------------------------
@router.get("/policies")
def get_library_policy(db: Session = Depends(get_db)):
    """
    Get current library policy settings.
    """
    try:
        policy = db.query(LibraryPolicy).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Library policy not found")
        
        return {
            "policy_id": policy.policy_id,
            "max_books_per_user": policy.max_books_per_user,
            "max_issue_days": policy.max_issue_days,
            "fine_per_day": policy.fine_per_day,
            "grace_period_days": policy.grace_period_days,
            "lost_book_penalty_multiplier": policy.lost_book_penalty_multiplier,
            "max_renewals": policy.max_renewals,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching policy: {str(e)}")


@router.put("/policies")
def update_library_policy(request: LibraryPolicyUpdate, db: Session = Depends(get_db)):
    """
    Update library policy settings.
    All fields are optional - only provided fields will be updated.
    """
    try:
        policy = db.query(LibraryPolicy).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Library policy not found")
        
        # Update only provided fields
        update_data = request.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        return {
            "message": "Policy updated successfully",
            "policy": {
                "policy_id": policy.policy_id,
                "max_books_per_user": policy.max_books_per_user,
                "max_issue_days": policy.max_issue_days,
                "fine_per_day": policy.fine_per_day,
                "grace_period_days": policy.grace_period_days,
                "lost_book_penalty_multiplier": policy.lost_book_penalty_multiplier,
                "max_renewals": policy.max_renewals,
                "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating policy: {str(e)}")
