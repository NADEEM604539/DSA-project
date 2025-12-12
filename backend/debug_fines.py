from db import SessionLocal
from models import UserFine
import json

db = SessionLocal()
fines = db.query(UserFine).filter(UserFine.user_id == 3).all()

print("Number of fines found:", len(fines))
for fine in fines:
    print(f"\nFine ID: {fine.fine_id}")
    print(f"Issue ID: {fine.issue_id}")
    print(f"Fine Type: {fine.fine_type}")
    print(f"Fine Type Value: {fine.fine_type.value if fine.fine_type else 'None'}")
    print(f"Amount: {fine.fine_amount}")
    print(f"Is Paid: {fine.is_paid}")
    print(f"Created At: {fine.created_at}")
    print(f"Created At ISO: {fine.created_at.isoformat() if fine.created_at else 'None'}")
    
    # Try creating the dict
    fine_dict = {
        "fine_id": fine.fine_id,
        "issue_id": fine.issue_id,
        "fine_type": fine.fine_type.value if fine.fine_type else "LATE_RETURN",
        "fine_amount": fine.fine_amount,
        "is_paid": fine.is_paid,
        "created_at": fine.created_at.isoformat() if fine.created_at else None,
        "paid_at": fine.paid_at.isoformat() if fine.paid_at else None
    }
    print("\nDict representation:")
    print(json.dumps(fine_dict, indent=2))

db.close()
