"""
routes/member.py

Role: Member endpoints for searching books, viewing their issued books, and fines.
- Search uses DSA structures (Trie for title/author prefix, AVL for sorted traversal, Hash for exact ISBN).
- Members cannot issue or return books directly; they can request searches and view their records.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from services.library import search_by_title, search_by_author, search_by_isbn
from models import Author

router = APIRouter(
    prefix="/member",
    tags=["Member"]
)

# ---------------------------
# Search Books by Title
# ---------------------------
@router.get("/search/title/{title_prefix}")
def member_search_title(title_prefix: str, db: Session = Depends(get_db)):
    """
    Search books by title prefix using Trie → AVL → Hash for fast DSA-based results.
    """
    results = search_by_title(db, title_prefix)
    if not results:
        raise HTTPException(status_code=404, detail="No books found")
    return {"books": results}


# ---------------------------
# Search Books by Author
# ---------------------------
@router.get("/search/author/{author_prefix}")
def member_search_author(author_prefix: str, db: Session = Depends(get_db)):
    """
    Search books by author prefix using Trie → AVL → Hash.
    """
    results = search_by_author(db, author_prefix)
    if not results:
        raise HTTPException(status_code=404, detail="No books found")
    return {"books": results}


# ---------------------------
# Search Book by ISBN (Exact Match)
# ---------------------------
@router.get("/search/isbn/{isbn}")
def member_search_isbn(isbn: str, db: Session = Depends(get_db)):
    """
    Search for a book by exact ISBN using Hash Table.
    """
    book = search_by_isbn(db, isbn)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"book": book}


# ---------------------------
# Get All Books
# ---------------------------
@router.get("/books")
def member_get_books(db: Session = Depends(get_db)):
    """
    Get all books in the library.
    """
    from models import Book, Author, Category
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


# ---------------------------
# Search Books (Generic)
# ---------------------------
@router.get("/search")
def member_search(q: str, db: Session = Depends(get_db)):
    """
    Generic search by title or author.
    """
    from models import Book
    results = db.query(Book).filter(
        (Book.title.ilike(f"%{q}%")) | 
        (Book.author_id.in_(db.query(Author.author_id).filter(Author.author_name.ilike(f"%{q}%"))))
    ).all()
    if not results:
        raise HTTPException(status_code=404, detail="No books found")
    return {"books": results}




# ---------------------------
# Get Member's Issued Books
# ---------------------------
@router.get("/my-issues/{user_id}")
def member_get_issues(user_id: int, db: Session = Depends(get_db)):
    """
    View all current and past book issues for the member.
    Returns enriched issue data with book title and author.
    """
    from models import IssueRecord, User, Book, Author
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        issues = db.query(IssueRecord).filter(IssueRecord.user_id == user_id).all()
        
        enriched_issues = []
        for issue in issues:
            book = db.query(Book).filter(Book.book_id == issue.book_id).first()
            author = None
            if book and book.author_id:
                author = db.query(Author).filter(Author.author_id == book.author_id).first()
            
            enriched_issues.append({
                "issue_id": issue.issue_id,
                "user_id": issue.user_id,
                "book_id": issue.book_id,
                "book_title": book.title if book else "Unknown",
                "author_name": author.author_name if author else "Unknown",
                "issue_date": issue.issued_at,
                "due_date": issue.due_date,
                "returned_at": issue.returned_at,
                "status": issue.status,
                "renewal_count": issue.renewal_count,
                "late_days": issue.late_days,
                "fine_amount": issue.fine_amount
            })
        
        return {"issues": enriched_issues, "count": len(enriched_issues)}
    except Exception as e:
        print(f"Error in member_get_issues: {str(e)}")
        return {"issues": [], "count": 0}


# ---------------------------
# Get Member's Fines
# ---------------------------
@router.get("/fines/{user_id}")
def member_get_fines(user_id: int, db: Session = Depends(get_db)):
    """
    View all fines (paid and unpaid) for the member with details.
    """
    from models import UserFine, User
    from fastapi.responses import JSONResponse
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        fines = db.query(UserFine).filter(UserFine.user_id == user_id).all()
        
        unpaid = sum([f.fine_amount for f in fines if not f.is_paid])
        paid = sum([f.fine_amount for f in fines if f.is_paid])
        
        # Format fine details
        fine_details = [
            {
                "fine_id": f.fine_id,
                "issue_id": f.issue_id,
                "fine_type": f.fine_type.value if f.fine_type else "LATE_RETURN",
                "fine_amount": float(f.fine_amount),
                "is_paid": f.is_paid,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "paid_at": f.paid_at.isoformat() if f.paid_at else None
            }
            for f in fines
        ]
        
        response_dict = {
            "user_id": user_id,
            "fines_count": len(fines),
            "summary": {
                "total_fines": float(unpaid + paid),
                "unpaid": float(unpaid),
                "paid": float(paid)
            },
            "fines": fine_details
        }
        
        return JSONResponse(content=response_dict)
    except Exception as e:
        print(f"ERROR in member_get_fines: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "user_id": user_id,
                "fines_count": 0,
                "summary": {
                    "total_fines": 0,
                    "unpaid": 0,
                    "paid": 0
                },
                "fines": []
            }
        )



# ---------------------------
# Renew Borrowed Book
# ---------------------------
@router.post("/renew/{issue_id}", response_model=None)
def member_renew_book(issue_id: int, db: Session = Depends(get_db)):
    """
    Renew a borrowed book if allowed by policy.
    Checks max renewals limit.
    """
    from models import IssueRecord, LibraryPolicy
    from services.library import renew_book
    
    issue = db.query(IssueRecord).filter(IssueRecord.issue_id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue record not found")
    if issue.returned_at:
        raise HTTPException(status_code=400, detail="Book already returned")
    
    policy = db.query(LibraryPolicy).first()
    if issue.renewal_count >= policy.max_renewals:
        raise HTTPException(status_code=400, detail="Maximum renewals exceeded")
    
    try:
        renewed_issue = renew_book(db, issue)
        return {
            "message": "Book renewed successfully",
            "new_due_date": renewed_issue.due_date,
            "renewals_used": renewed_issue.renewal_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------
# Request Book Return
# ---------------------------
@router.post("/request-return/{issue_id}")
def member_request_return(issue_id: int, db: Session = Depends(get_db)):
    """
    Member requests to return a borrowed book.
    Librarian will need to process the return.
    Sets status to RETURN_REQUESTED.
    """
    try:
        from models import IssueRecord, IssueStatus
        
        issue = db.query(IssueRecord).filter(IssueRecord.issue_id == issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue record not found")
        
        if issue.returned_at:
            raise HTTPException(status_code=400, detail="Book already returned")
        if issue.status == IssueStatus.RETURN_REQUESTED:
            raise HTTPException(status_code=400, detail="Return already requested")
        
        # Update status to RETURN_REQUESTED
        issue.status = IssueStatus.RETURN_REQUESTED
        db.add(issue)
        db.commit()
        db.refresh(issue)
        
        return {
            "message": "Return request submitted successfully",
            "issue_id": issue_id,
            "status": "return_requested"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing return request: {str(e)}")


# ---------------------------
# Cancel Book Return Request
# ---------------------------
@router.post("/cancel-return/{issue_id}")
def member_cancel_return(issue_id: int, db: Session = Depends(get_db)):
    """
    Member cancels a pending return request.
    Moves the book back to APPROVED status (actively borrowed).
    """
    try:
        from models import IssueRecord, IssueStatus
        
        issue = db.query(IssueRecord).filter(IssueRecord.issue_id == issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue record not found")
        
        if issue.status != IssueStatus.RETURN_REQUESTED:
            raise HTTPException(status_code=400, detail="Return has not been requested for this book")
        
        # Update status back to APPROVED (actively borrowed)
        issue.status = IssueStatus.APPROVED
        db.add(issue)
        db.commit()
        db.refresh(issue)
        
        return {
            "message": "Return request cancelled successfully",
            "issue_id": issue_id,
            "status": "approved"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error cancelling return request: {str(e)}")


# ---------------------------
# Download Fine Challan PDF
# ---------------------------
@router.get("/fines/{fine_id}/challan")
def download_fine_challan(fine_id: int, user_id: int, db: Session = Depends(get_db)):
    """
    Download fine challan as PDF.
    Query params: fine_id (path), user_id (query)
    """
    from models import UserFine
    from services.pdf_generator import generate_fine_challan
    from fastapi.responses import StreamingResponse
    
    try:
        # Verify the fine belongs to the user
        fine = db.query(UserFine).filter(
            UserFine.fine_id == fine_id,
            UserFine.user_id == user_id
        ).first()
        
        if not fine:
            raise HTTPException(status_code=404, detail="Fine record not found")
        
        # Generate PDF
        pdf_buffer = generate_fine_challan(user_id, fine_id, db)
        
        if not pdf_buffer:
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        return StreamingResponse(
            iter([pdf_buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=fine_challan_{fine_id}.pdf"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


# ---------------------------
# Mark Fine as Paid
# ---------------------------
@router.post("/fines/{fine_id}/mark-paid")
def mark_fine_paid(fine_id: int, db: Session = Depends(get_db)):
    """
    Mark a fine as paid (admin action for fines management page)
    """
    from models import UserFine
    from datetime import datetime
    
    try:
        fine = db.query(UserFine).filter(UserFine.fine_id == fine_id).first()
        
        if not fine:
            raise HTTPException(status_code=404, detail="Fine not found")
        
        # Mark as paid
        fine.is_paid = True
        fine.paid_at = datetime.now()
        
        db.commit()
        db.refresh(fine)
        
        return {
            "message": "Fine marked as paid successfully",
            "fine_id": fine_id,
            "amount": fine.fine_amount,
            "paid_at": fine.paid_at.isoformat() if fine.paid_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error marking fine as paid: {str(e)}")


# ---------------------------
# Approve Return Request
# ---------------------------
@router.post("/return-requests/{request_id}/approve")
def approve_return_request(request_id: int, db: Session = Depends(get_db)):
    """
    Approve a return request (admin action)
    """
    try:
        from models import ReturnRequest
        from datetime import datetime
        
        request = db.query(ReturnRequest).filter(ReturnRequest.request_id == request_id).first()
        
        if not request:
            raise HTTPException(status_code=404, detail="Return request not found")
        
        request.status = 'APPROVED'
        request.approved_at = datetime.now()
        
        db.commit()
        db.refresh(request)
        
        return {
            "message": "Return request approved",
            "request_id": request_id,
            "status": request.status
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error approving request: {str(e)}")


# ---------------------------
# Reject Return Request
# ---------------------------
@router.post("/return-requests/{request_id}/reject")
def reject_return_request(request_id: int, db: Session = Depends(get_db)):
    """
    Reject a return request (admin action)
    """
    try:
        from models import ReturnRequest
        from datetime import datetime
        
        request = db.query(ReturnRequest).filter(ReturnRequest.request_id == request_id).first()
        
        if not request:
            raise HTTPException(status_code=404, detail="Return request not found")
        
        request.status = 'REJECTED'
        request.rejected_at = datetime.now()
        
        db.commit()
        db.refresh(request)
        
        return {
            "message": "Return request rejected",
            "request_id": request_id,
            "status": request.status
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error rejecting request: {str(e)}")


# ---------------------------
# Approve Issue Request
# ---------------------------
@router.post("/issue-requests/{request_id}/approve")
def approve_issue_request(request_id: int, db: Session = Depends(get_db)):
    """
    Approve an issue request (admin action)
    """
    try:
        from models import IssueRequest
        from datetime import datetime
        
        request = db.query(IssueRequest).filter(IssueRequest.issue_request_id == request_id).first()
        
        if not request:
            raise HTTPException(status_code=404, detail="Issue request not found")
        
        request.status = 'APPROVED'
        request.approved_at = datetime.now()
        
        db.commit()
        db.refresh(request)
        
        return {
            "message": "Issue request approved",
            "request_id": request_id,
            "status": request.status
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error approving request: {str(e)}")


# ---------------------------
# Reject Issue Request
# ---------------------------
@router.post("/issue-requests/{request_id}/reject")
def reject_issue_request(request_id: int, db: Session = Depends(get_db)):
    """
    Reject an issue request (admin action)
    """
    try:
        from models import IssueRequest
        from datetime import datetime
        
        request = db.query(IssueRequest).filter(IssueRequest.issue_request_id == request_id).first()
        
        if not request:
            raise HTTPException(status_code=404, detail="Issue request not found")
        
        request.status = 'REJECTED'
        request.rejected_at = datetime.now()
        
        db.commit()
        db.refresh(request)
        
        return {
            "message": "Issue request rejected",
            "request_id": request_id,
            "status": request.status
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error rejecting request: {str(e)}")


# ---------------------------
# Extend Issue Deadline
# ---------------------------
@router.post("/issues/{issue_id}/extend")
def extend_issue_deadline(issue_id: int, additional_days: int = 7, db: Session = Depends(get_db)):
    """
    Extend the deadline for an issue (renewal/extension)
    """
    try:
        from models import IssueRecord
        from datetime import timedelta
        
        issue = db.query(IssueRecord).filter(IssueRecord.issue_id == issue_id).first()
        
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        if issue.returned_at:
            raise HTTPException(status_code=400, detail="Cannot extend a returned book")
        
        # Extend the due date
        old_due_date = issue.due_date
        issue.due_date = issue.due_date + timedelta(days=additional_days)
        
        db.commit()
        db.refresh(issue)
        
        return {
            "message": f"Issue deadline extended by {additional_days} days",
            "issue_id": issue_id,
            "old_due_date": old_due_date.isoformat() if old_due_date else None,
            "new_due_date": issue.due_date.isoformat() if issue.due_date else None
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error extending deadline: {str(e)}")


# ---------------------------
# General Announcements
# ---------------------------
@router.get("/announcements")
def member_get_announcements(db: Session = Depends(get_db)):
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
def member_get_notifications(user_id: int, db: Session = Depends(get_db)):
    """
    Get all notifications/announcements for a member.
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
