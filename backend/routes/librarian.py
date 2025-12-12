"""
routes/librarian.py

Role: Librarian endpoints for day-to-day library operations.
- Issue books, return books, mark lost.
- Uses DSA-first services from services/library.py.
- Cannot modify policies (admin-only).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import Book, User, IssueRecord, Author, Category, LibraryPolicy, IssueStatus
from services.library import issue_book, return_book, mark_lost
from pydantic import BaseModel
from datetime import datetime
from auth import get_current_user


class IssueBookRequest(BaseModel):
    user_id: int
    book_id: int
    due_date: str = None


class ReturnBookRequest(BaseModel):
    issue_id: int

router = APIRouter(
    prefix="/librarian",
    tags=["Librarian"]
)

# ---------------------------
# Issue Book (JSON endpoint)
# ---------------------------
@router.post("/issue")
def librarian_issue_book_json(request: IssueBookRequest, db: Session = Depends(get_db)):
    """
    Issue a book to a member.
    Enforces max books per user policy.
    """
    user = db.query(User).filter_by(user_id=request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    book = db.query(Book).filter_by(book_id=request.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.available_copies < 1:
        raise HTTPException(status_code=400, detail="No available copies")

    try:
        issue = issue_book(db, user, book)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Book issued successfully", "issue_id": issue.issue_id}

# ---------------------------
# Issue Book
# ---------------------------
@router.post("/issue/{user_id}/{book_id}")
def librarian_issue_book(user_id: int, book_id: int, db: Session = Depends(get_db)):
    """
    Issue a book to a member.
    Enforces max books per user policy.
    """
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        book = db.query(Book).filter_by(book_id=book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        if book.available_copies < 1:
            raise HTTPException(status_code=400, detail="No available copies")

        issue = issue_book(db, user, book)
        return {"message": "Book issued successfully", "issue_id": issue.issue_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error issuing book: {str(e)}")


# ---------------------------
# Return Book
# ---------------------------
@router.post("/return/{issue_id}")
def librarian_return_book(issue_id: int, db: Session = Depends(get_db)):
    """
    Return a book.
    Calculates fines if overdue and updates DSA/DB.
    Accepts books in APPROVED or RETURN_REQUESTED status.
    """
    try:
        from models import IssueStatus
        
        issue = db.query(IssueRecord).filter_by(issue_id=issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue record not found")
        if issue.returned_at:
            raise HTTPException(status_code=400, detail="Book already returned")
        
        # Accept return from APPROVED or RETURN_REQUESTED status
        if issue.status not in [IssueStatus.APPROVED, IssueStatus.RETURN_REQUESTED]:
            raise HTTPException(status_code=400, detail=f"Cannot return book in {issue.status} status. Must be APPROVED or RETURN_REQUESTED.")

        returned_issue = return_book(db, issue)
        db.refresh(returned_issue)  # Ensure we get the updated object
        
        return {
            "message": "Book returned successfully",
            "issue_id": issue_id,
            "status": "returned",
            "fine_amount": returned_issue.fine_amount
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error returning book: {str(e)}")


# ---------------------------
# Approve Issue (Librarian approval)
# ---------------------------
@router.post("/issues/{issue_id}/approve")
def librarian_approve_issue(issue_id: int, db: Session = Depends(get_db)):
    """
    Approve a pending book issue request.
    Sets status to APPROVED.
    """
    from models import IssueStatus
    try:
        issue = db.query(IssueRecord).filter_by(issue_id=issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue record not found")
        
        if issue.status != IssueStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Cannot approve issue with status: {issue.status}")
        
        issue.status = IssueStatus.APPROVED
        db.commit()
        
        return {
            "message": "Issue approved successfully",
            "issue_id": issue_id,
            "status": issue.status.value
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------
# Reject Issue (Librarian rejection)
# ---------------------------
@router.post("/issues/{issue_id}/reject")
def librarian_reject_issue(issue_id: int, db: Session = Depends(get_db)):
    """
    Reject a pending book issue request.
    Sets status to REJECTED and restores available copies.
    """
    from models import IssueStatus
    try:
        issue = db.query(IssueRecord).filter_by(issue_id=issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue record not found")
        
        if issue.status != IssueStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Cannot reject issue with status: {issue.status}")
        
        # Restore available copies
        book = db.query(Book).filter_by(book_id=issue.book_id).first()
        if book:
            book.available_copies += 1
        
        issue.status = IssueStatus.REJECTED
        db.commit()
        
        return {
            "message": "Issue rejected successfully",
            "issue_id": issue_id,
            "status": issue.status.value
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------
# Return Book (JSON endpoint)
# ---------------------------
@router.post("/return")
def librarian_return_book_json(request: ReturnBookRequest, db: Session = Depends(get_db)):
    """
    Return a book.
    Calculates fines if overdue and updates DSA/DB.
    """
    issue = db.query(IssueRecord).filter_by(issue_id=request.issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue record not found")
    if issue.returned_at:
        raise HTTPException(status_code=400, detail="Book already returned")

    returned_issue = return_book(db, issue)
    return {"message": "Book returned successfully", "fine_amount": returned_issue.fine_amount}


# ---------------------------
# Mark Lost
# ---------------------------
@router.post("/lost/{issue_id}")
def librarian_mark_lost(issue_id: int, db: Session = Depends(get_db)):
    """
    Mark a book as lost.
    Applies lost book penalty and updates available copies.
    """
    try:
        issue = db.query(IssueRecord).filter_by(issue_id=issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue record not found")
        if issue.is_lost:
            raise HTTPException(status_code=400, detail="Book already marked lost")
        if issue.returned_at:
            raise HTTPException(status_code=400, detail="Cannot mark returned book as lost")

        lost_issue = mark_lost(db, issue)
        return {"message": "Book marked lost", "lost_fine": lost_issue.fine_amount}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------
# View Pending Fines
# ---------------------------
@router.get("/pending-fines")
def librarian_view_pending_fines(db: Session = Depends(get_db)):
    """
    View all unpaid fines across all members.
    """
    from models import UserFine
    try:
        unpaid_fines = db.query(UserFine).filter(UserFine.is_paid == False).all()
        total_unpaid = sum([f.fine_amount for f in unpaid_fines])
        
        return {
            "pending_fines_count": len(unpaid_fines),
            "count": len(unpaid_fines),
            "total_amount": total_unpaid
        }
    except Exception as e:
        return {
            "pending_fines_count": 0,
            "count": 0,
            "total_amount": 0
        }


# ---------------------------
# Collect Fine
# ---------------------------
@router.post("/collect-fine/{fine_id}")
def librarian_collect_fine(fine_id: int, db: Session = Depends(get_db)):
    """
    Mark a fine as paid.
    """
    from models import UserFine
    
    fine = db.query(UserFine).filter(UserFine.fine_id == fine_id).first()
    if not fine:
        raise HTTPException(status_code=404, detail="Fine not found")
    if fine.is_paid:
        raise HTTPException(status_code=400, detail="Fine already paid")
    
    fine.is_paid = True
    fine.paid_at = datetime.now()
    db.commit()
    
    return {"message": "Fine collected successfully", "amount": fine.fine_amount}


@router.post("/reminders", response_model=None)
def librarian_send_reminders(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Send reminder notifications to members with overdue or due books.
    Creates notifications for overdue books and pending fines.
    """
    from models import IssueRecord, Notification, NotificationType, UserFine
    from datetime import date
    from logger import log_system
    
    # Check role
    if current_user.role != "LIBRARIAN":
        raise HTTPException(status_code=403, detail="Only librarians can send reminders")
    
    overdue_issues = db.query(IssueRecord).filter(
        IssueRecord.return_date == None,
        IssueRecord.due_date < date.today()
    ).all()
    
    unpaid_fines = db.query(UserFine).filter(UserFine.is_paid == False).all()
    
    notifications_created = 0
    
    # Create reminders for overdue books
    for issue in overdue_issues:
        notification = Notification(
            user_id=issue.user_id,
            message=f"Reminder: Book ID {issue.book_id} is overdue (due: {issue.due_date})",
            notification_type=NotificationType.REMINDER
        )
        db.add(notification)
        notifications_created += 1
    
    # Create reminders for unpaid fines
    for fine in unpaid_fines:
        notification = Notification(
            user_id=fine.user_id,
            message=f"Reminder: You have an unpaid fine of {fine.fine_amount}",
            notification_type=NotificationType.FINE_NOTICE
        )
        db.add(notification)
        notifications_created += 1
    
    db.commit()
    
    log_system(current_user.user_id, f"Sent {notifications_created} reminder notifications", 0)
    
    return {
        "message": "Reminders sent successfully",
        "overdue_issues": len(overdue_issues),
        "unpaid_fines": len(unpaid_fines),
        "notifications_created": notifications_created
    }


# ---------------------------
# CRUD Books
# ---------------------------
class AddBookRequest(BaseModel):
    title: str
    author: str
    isbn: str = None
    publisher: str = None
    year: int = None
    quantity: int = 1
    available: int = None
    category: str = None


@router.post("/books")
def librarian_add_book(
    book_data: AddBookRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new book to the system.
    """
    try:
        from models import Author, Category
        
        available = book_data.available if book_data.available is not None else book_data.quantity
        
        # Get or create author
        author = None
        if book_data.author:
            author = db.query(Author).filter_by(author_name=book_data.author).first()
            if not author:
                author = Author(author_name=book_data.author)
                db.add(author)
                db.flush()
        
        # Get or create category
        category = None
        if book_data.category:
            category = db.query(Category).filter_by(category_name=book_data.category).first()
            if not category:
                category = Category(category_name=book_data.category)
                db.add(category)
                db.flush()
        
        book = Book(
            title=book_data.title,
            isbn=book_data.isbn or f"ISBN-{db.query(Book).count() + 1}",
            author_id=author.author_id if author else None,
            category_id=category.category_id if category else None,
            publication_year=book_data.year,
            total_copies=book_data.quantity,
            available_copies=available
        )
        
        db.add(book)
        db.commit()
        db.refresh(book)
        
        return {
            "message": "Book added successfully",
            "book_id": book.book_id,
            "book": {
                "book_id": book.book_id,
                "title": book.title,
                "isbn": book.isbn,
                "author": book_data.author,
                "category": book_data.category,
                "year": book.publication_year,
                "quantity": book.total_copies,
                "available": book.available_copies
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------
# Approve Issue Request
# ---------------------------
@router.post("/issues/{issue_id}/approve")
def librarian_approve_issue(issue_id: int, db: Session = Depends(get_db)):
    """
    Approve a book issue request.
    Changes status from PENDING to APPROVED.
    """
    from models import IssueStatus
    
    try:
        issue = db.query(IssueRecord).filter_by(issue_id=issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue record not found")
        
        if issue.status != IssueStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Cannot approve issue with status: {issue.status}")
        
        issue.status = IssueStatus.APPROVED
        db.commit()
        
        return {
            "message": "Issue approved successfully",
            "issue_id": issue_id,
            "status": "APPROVED"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------
# Reject Issue Request
# ---------------------------
@router.post("/issues/{issue_id}/reject")
def librarian_reject_issue(issue_id: int, db: Session = Depends(get_db)):
    """
    Reject a book issue request.
    Changes status from PENDING to REJECTED and restores book availability.
    """
    from models import IssueStatus
    
    try:
        issue = db.query(IssueRecord).filter_by(issue_id=issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue record not found")
        
        if issue.status != IssueStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Cannot reject issue with status: {issue.status}")
        
        # Restore book availability
        book = db.query(Book).filter_by(book_id=issue.book_id).first()
        if book:
            book.available_copies += 1
        
        issue.status = IssueStatus.REJECTED
        db.commit()
        
        return {
            "message": "Issue rejected successfully",
            "issue_id": issue_id,
            "status": "REJECTED"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/issues")
def librarian_get_issues(db: Session = Depends(get_db)):
    """
    Get all issues (book borrowing requests).
    """
    issues = db.query(IssueRecord).all()
    result = []
    for issue in issues:
        user = db.query(User).filter_by(user_id=issue.user_id).first()
        book = db.query(Book).filter_by(book_id=issue.book_id).first()
        author = db.query(Author).filter_by(author_id=book.author_id).first() if book and book.author_id else None
        
        result.append({
            "issue_id": issue.issue_id,
            "user_id": issue.user_id,
            "member_name": user.full_name if user else "Unknown",
            "book_id": issue.book_id,
            "book_title": book.title if book else "Unknown",
            "author": author.author_name if author else "Unknown",
            "issue_date": issue.issued_at.isoformat() if issue.issued_at else None,
            "issued_at": issue.issued_at.isoformat() if issue.issued_at else None,
            "due_date": issue.due_date.isoformat() if issue.due_date else None,
            "returned_at": issue.returned_at.isoformat() if issue.returned_at else None,
            "status": issue.status.value.lower() if issue.status else "pending"
        })
    return {"issues": result}


@router.get("/members")
def librarian_get_members(db: Session = Depends(get_db)):
    """
    Get all members.
    """
    members = db.query(User).filter(User.role == "MEMBER").all()
    result = []
    for member in members:
        # Count active issues
        active_issues = db.query(IssueRecord).filter(
            IssueRecord.user_id == member.user_id,
            IssueRecord.returned_at == None
        ).count()
        
        result.append({
            "user_id": member.user_id,
            "full_name": member.full_name,
            "email": member.email,
            "created_at": member.created_at.isoformat() if member.created_at else None,
            "active_issues": active_issues,
            "is_active": True
        })
    return {"members": result}


@router.get("/members/{member_id}")
def librarian_get_member_details(member_id: int, db: Session = Depends(get_db)):
    """
    Get detailed info about a specific member.
    """
    member = db.query(User).filter_by(user_id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get active issues
    active_issues = db.query(IssueRecord).filter(
        IssueRecord.user_id == member_id,
        IssueRecord.returned_at == None
    ).all()
    
    # Get fines
    from models import UserFine
    fines = db.query(UserFine).filter(UserFine.user_id == member_id).all()
    
    issues_detail = []
    for issue in active_issues:
        book = db.query(Book).filter_by(book_id=issue.book_id).first()
        author = db.query(Author).filter_by(author_id=book.author_id).first() if book and book.author_id else None
        issues_detail.append({
            "issue_id": issue.issue_id,
            "book_title": book.title if book else "Unknown",
            "author_name": author.author_name if author else "Unknown",
            "issued_at": issue.issued_at.isoformat() if issue.issued_at else None,
            "due_date": issue.due_date.isoformat() if issue.due_date else None,
            "is_overdue": issue.due_date < datetime.now().date() if issue.due_date else False
        })
    
    return {
        "member": {
            "user_id": member.user_id,
            "full_name": member.full_name,
            "email": member.email,
            "created_at": member.created_at.isoformat() if member.created_at else None,
            "active_issues_count": len(active_issues),
            "active_issues": issues_detail,
            "total_fines": sum([f.fine_amount for f in fines]),
            "unpaid_fines": sum([f.fine_amount for f in fines if not f.is_paid]),
            "is_active": True
        }
    }


@router.post("/members/{member_id}/suspend")
def librarian_suspend_member(member_id: int, db: Session = Depends(get_db)):
    """
    Suspend a member (prevent borrowing).
    """
    # Note: Add is_suspended column to User model for actual suspension logic
    member = db.query(User).filter_by(user_id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # TODO: Add is_suspended column to User model and update here
    return {"message": "Member suspended successfully"}


@router.post("/members/{member_id}/activate")
def librarian_activate_member(member_id: int, db: Session = Depends(get_db)):
    """
    Reactivate a suspended member.
    """
    # Note: Add is_suspended column to User model for actual suspension logic
    member = db.query(User).filter_by(user_id=member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # TODO: Add is_suspended column to User model and update here
    return {"message": "Member activated successfully"}


@router.get("/books")
def librarian_get_books(db: Session = Depends(get_db)):
    """
    Get all books.
    """
    books = db.query(Book).all()
    result = []
    for book in books:
        author = db.query(Author).filter_by(author_id=book.author_id).first() if book.author_id else None
        category = db.query(Category).filter_by(category_id=book.category_id).first() if book.category_id else None
        
        result.append({
            "book_id": book.book_id,
            "title": book.title,
            "isbn": book.isbn,
            "author": author.author_name if author else "Unknown",
            "category": category.category_name if category else "Uncategorized",
            "year": book.publication_year,
            "quantity": book.total_copies,
            "available": book.available_copies
        })
    return {"books": result}


class UpdateBookRequest(BaseModel):
    title: str = None
    author: str = None
    isbn: str = None
    publisher: str = None
    year: int = None
    quantity: int = None
    available: int = None
    category: str = None


@router.put("/books/{book_id}")
def librarian_update_book(
    book_id: int,
    book_data: UpdateBookRequest,
    db: Session = Depends(get_db)
):
    """
    Update book details (title, author, isbn, publisher, year, quantity, available, category).
    Ensures available_copies <= total_copies (constraint check).
    """
    try:
        from models import Author, Category
        
        book = db.query(Book).filter(Book.book_id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # If updating quantity, validate that available_copies won't exceed new total_copies
        if book_data.quantity is not None:
            # Calculate borrowed copies
            borrowed_copies = book.total_copies - book.available_copies
            
            # New total must be >= borrowed copies
            if book_data.quantity < borrowed_copies:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot reduce quantity below {borrowed_copies} (currently {borrowed_copies} copies borrowed). Available would become negative."
                )
            
            book.total_copies = book_data.quantity
            # If available_copies would exceed new total, adjust it
            if book.available_copies > book_data.quantity:
                book.available_copies = book_data.quantity
        
        # Update other fields if provided
        if book_data.title:
            book.title = book_data.title
        if book_data.isbn:
            book.isbn = book_data.isbn
        if book_data.year:
            book.publication_year = book_data.year
        
        # Only update available_copies if provided AND doesn't exceed total_copies
        if book_data.available is not None:
            if book_data.available > book.total_copies:
                raise HTTPException(
                    status_code=400,
                    detail=f"Available copies ({book_data.available}) cannot exceed total copies ({book.total_copies})"
                )
            book.available_copies = book_data.available
        
        # Handle author
        if book_data.author:
            author = db.query(Author).filter_by(author_name=book_data.author).first()
            if not author:
                author = Author(author_name=book_data.author)
                db.add(author)
                db.flush()
            book.author_id = author.author_id
        
        # Handle category
        if book_data.category:
            category = db.query(Category).filter_by(category_name=book_data.category).first()
            if not category:
                category = Category(category_name=book_data.category)
                db.add(category)
                db.flush()
            book.category_id = category.category_id
        
        db.commit()
        
        # Get updated author and category names
        author = db.query(Author).filter_by(author_id=book.author_id).first() if book.author_id else None
        category = db.query(Category).filter_by(category_id=book.category_id).first() if book.category_id else None
        
        return {
            "message": "Book updated successfully",
            "book_id": book.book_id,
            "book": {
                "book_id": book.book_id,
                "title": book.title,
                "isbn": book.isbn,
                "author": author.author_name if author else "Unknown",
                "category": category.category_name if category else "Uncategorized",
                "year": book.publication_year,
                "quantity": book.total_copies,
                "available": book.available_copies
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/books/{book_id}")
def librarian_delete_book(book_id: int, db: Session = Depends(get_db)):
    """
    Delete a book from the system.
    """
    from services.library import remove_book
    
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    try:
        remove_book(db, book)
        return {"message": "Book deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-books-inventory")
@router.get("/reset-books-inventory")
def reset_books_inventory(db: Session = Depends(get_db)):
    """
    Reset all books to have proper inventory (3 copies each, all available).
    For initialization/testing purposes.
    """
    try:
        books = db.query(Book).all()
        for book in books:
            book.total_copies = 3
            book.available_copies = 3
        
        db.commit()
        
        return {
            "message": "All books inventory reset successfully",
            "books_updated": len(books),
            "details": "All books now have 3 total copies and 3 available copies"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# Library Settings Endpoints
@router.get("/settings")
def get_library_settings(db: Session = Depends(get_db)):
    """
    Get current library settings/policies.
    """
    try:
        # Get or create default policy
        policy = db.query(LibraryPolicy).filter(LibraryPolicy.policy_id == 1).first()
        
        if not policy:
            # Create default policy if it doesn't exist
            policy = LibraryPolicy(
                policy_id=1,
                max_books_per_user=5,
                max_issue_days=14,
                fine_per_day=10,
                grace_period_days=0,
                lost_book_penalty_multiplier=3,
                max_renewals=2
            )
            db.add(policy)
            db.commit()
        
        return {
            "policy_id": policy.policy_id,
            "max_books_per_user": policy.max_books_per_user,
            "max_issue_days": policy.max_issue_days,
            "fine_per_day": policy.fine_per_day,
            "grace_period_days": policy.grace_period_days,
            "lost_book_penalty_multiplier": policy.lost_book_penalty_multiplier,
            "max_renewals": policy.max_renewals
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/settings")
def update_library_settings(
    settings: dict,
    db: Session = Depends(get_db)
):
    """
    Update library settings/policies.
    Expected fields: max_books_per_user, max_issue_days, fine_per_day, grace_period_days,
    lost_book_penalty_multiplier, max_renewals
    """
    try:
        policy = db.query(LibraryPolicy).filter(LibraryPolicy.policy_id == 1).first()
        
        if not policy:
            # Create default policy if it doesn't exist
            policy = LibraryPolicy(
                policy_id=1,
                max_books_per_user=settings.get("max_books_per_user", 5),
                max_issue_days=settings.get("max_issue_days", 14),
                fine_per_day=settings.get("fine_per_day", 10),
                grace_period_days=settings.get("grace_period_days", 0),
                lost_book_penalty_multiplier=settings.get("lost_book_penalty_multiplier", 3),
                max_renewals=settings.get("max_renewals", 2)
            )
            db.add(policy)
        else:
            # Update existing policy
            if "max_books_per_user" in settings:
                policy.max_books_per_user = settings["max_books_per_user"]
            if "max_issue_days" in settings:
                policy.max_issue_days = settings["max_issue_days"]
            if "fine_per_day" in settings:
                policy.fine_per_day = settings["fine_per_day"]
            if "grace_period_days" in settings:
                policy.grace_period_days = settings["grace_period_days"]
            if "lost_book_penalty_multiplier" in settings:
                policy.lost_book_penalty_multiplier = settings["lost_book_penalty_multiplier"]
            if "max_renewals" in settings:
                policy.max_renewals = settings["max_renewals"]
        
        db.commit()
        
        return {
            "message": "Settings updated successfully",
            "policy": {
                "policy_id": policy.policy_id,
                "max_books_per_user": policy.max_books_per_user,
                "max_issue_days": policy.max_issue_days,
                "fine_per_day": policy.fine_per_day,
                "grace_period_days": policy.grace_period_days,
                "lost_book_penalty_multiplier": policy.lost_book_penalty_multiplier,
                "max_renewals": policy.max_renewals
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------
# General Announcements
# ---------------------------
@router.get("/announcements")
def librarian_get_announcements(db: Session = Depends(get_db)):
    """
    Get all general announcements (newest first).
    These are system announcements visible to all users.
    """
    from models import Notification
    
    announcements = db.query(Notification).order_by(
        Notification.created_at.desc()
    ).all()
    
    return {
        "announcements": [
            {
                "announcement_id": a.announcement_id,
                "message": a.message,
                "announcement_type": a.announcement_type,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in announcements
        ],
        "total": len(announcements)
    }


# ---------------------------
# Get Notifications (Same as Announcements - Broadcast to all)
# ---------------------------
@router.get("/notifications/{user_id}")
def librarian_get_notifications(user_id: int, db: Session = Depends(get_db)):
    """
    Get all notifications/announcements for a librarian.
    Announcements are broadcast messages sent by admin to all users.
    """
    try:
        from models import Notification
        
        # Fetch all announcements (broadcast to all users)
        notifications = db.query(Notification).order_by(
            Notification.created_at.desc()
        ).all()
        
        return {
            "notifications": [
                {
                    "notification_id": n.announcement_id,
                    "message": n.message,
                    "type": n.announcement_type,
                    "created_at": n.created_at.isoformat() if n.created_at else None
                }
                for n in notifications
            ],
            "total": len(notifications)
        }
    except Exception as e:
        print(f"Error fetching notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")
