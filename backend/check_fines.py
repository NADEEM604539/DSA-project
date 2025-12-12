from db import SessionLocal
from models import UserFine

db = SessionLocal()
fines = db.query(UserFine).filter(UserFine.user_id == 3).all()
print(f"Total fines for user 3: {len(fines)}")
for fine in fines:
    print(f"\nFine ID: {fine.fine_id}")
    print(f"Issue ID: {fine.issue_id}")
    print(f"Fine Type: {fine.fine_type}")
    print(f"Amount: ${fine.fine_amount}")
    print(f"Is Paid: {fine.is_paid}")
    print(f"Created At: {fine.created_at}")

db.close()
