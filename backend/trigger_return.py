from db import SessionLocal
from models import IssueRecord
from services.library import return_book
from datetime import datetime, timedelta

db = SessionLocal()
issue = db.query(IssueRecord).filter(IssueRecord.issue_id == 1).first()
if issue:
    # Set the due date to 10 days ago to make it late
    issue.due_date = datetime.now() - timedelta(days=10)
    db.commit()
    
    print(f"Calling return_book for issue {issue.issue_id}")
    print(f"Due date: {issue.due_date}")
    
    # Call return_book which should generate the fine
    returned = return_book(db, issue)
    
    print(f"\n✓ Book returned!")
    print(f"Status: {returned.status}")
    print(f"Late days: {returned.late_days}")
    print(f"Fine amount: {returned.fine_amount}")

db.close()
