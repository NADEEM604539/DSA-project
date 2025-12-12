#!/usr/bin/env python
"""
Migration script to add status column to issue_records table.
"""

from sqlalchemy import text
from db import engine

def migrate():
    with engine.connect() as conn:
        # Add status column if it doesn't exist
        try:
            # First check if column exists by describing the table
            result = conn.execute(text("DESCRIBE issue_records"))
            columns = [row[0] for row in result]
            
            if 'status' in columns:
                print("✓ Status column already exists")
                return
            
            # Column doesn't exist, add it
            conn.execute(text("ALTER TABLE issue_records ADD COLUMN status VARCHAR(50) DEFAULT 'PENDING'"))
            conn.commit()
            print("✓ Status column added to issue_records")
            
            # Update existing records - set status based on returned_at
            conn.execute(text("UPDATE issue_records SET status = 'RETURNED' WHERE returned_at IS NOT NULL"))
            conn.execute(text("UPDATE issue_records SET status = 'APPROVED' WHERE returned_at IS NULL"))
            conn.commit()
            print("✓ Existing records updated with status")
            
        except Exception as e:
            print(f"✗ Migration error: {str(e)}")
            raise

if __name__ == "__main__":
    print("Starting migration...")
    migrate()
    print("Migration complete!")
