from db import SessionLocal
from models import IssueRecord

db = SessionLocal()
issue = db.query(IssueRecord).filter(IssueRecord.issue_id == 1).first()
if issue:
    print(f"Issue ID: {issue.issue_id}")
    print(f"User ID: {issue.user_id}")
    print(f"Status: {issue.status}")
    print(f"Due Date: {issue.due_date}")
    print(f"Returned At: {issue.returned_at}")
    print(f"Fine Amount: {issue.fine_amount}")
db.close()
