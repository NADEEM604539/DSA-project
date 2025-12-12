#!/usr/bin/env python3
"""
Seed data script - Populates the library database with test data
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import sys

def seed_database():
    """Add test data to the database"""
    try:
        # Create engine for the library database
        engine = create_engine(
            "mysql+pymysql://root:NdM604539@127.0.0.1:3306/library",
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Import models
        from models import (
            User, UserRole, Author, Category, Book, IssueRecord, 
            IssueStatus, UserFine, FineType, Notification, NotificationType
        )
        
        print("🔄 Seeding database with test data...\n")
        
        # ============================================
        # 1) ADD USERS
        # ============================================
        print("📝 Adding users...")
        users = [
            User(full_name="Admin User", email="admin@library.com", role=UserRole.ADMIN),
            User(full_name="Librarian Sarah", email="librarian@library.com", role=UserRole.LIBRARIAN),
            User(full_name="John Doe", email="john@example.com", role=UserRole.MEMBER),
            User(full_name="Jane Smith", email="jane@example.com", role=UserRole.MEMBER),
            User(full_name="Bob Wilson", email="bob@example.com", role=UserRole.MEMBER),
            User(full_name="Alice Johnson", email="alice@example.com", role=UserRole.MEMBER),
            User(full_name="Charlie Brown", email="charlie@example.com", role=UserRole.MEMBER),
            User(full_name="Diana Prince", email="diana@example.com", role=UserRole.MEMBER),
        ]
        session.add_all(users)
        session.commit()
        print(f"   ✓ Added {len(users)} users")
        
        # ============================================
        # 2) ADD AUTHORS
        # ============================================
        print("📝 Adding authors...")
        authors = [
            Author(author_name="J.K. Rowling"),
            Author(author_name="George R.R. Martin"),
            Author(author_name="J.R.R. Tolkien"),
            Author(author_name="Stephen King"),
            Author(author_name="Agatha Christie"),
            Author(author_name="Isaac Asimov"),
            Author(author_name="Margaret Atwood"),
            Author(author_name="Haruki Murakami"),
        ]
        session.add_all(authors)
        session.commit()
        print(f"   ✓ Added {len(authors)} authors")
        
        # ============================================
        # 3) ADD CATEGORIES
        # ============================================
        print("📝 Adding categories...")
        categories = [
            Category(category_name="Fantasy"),
            Category(category_name="Science Fiction"),
            Category(category_name="Mystery"),
            Category(category_name="Horror"),
            Category(category_name="Romance"),
            Category(category_name="Literary Fiction"),
            Category(category_name="Thriller"),
            Category(category_name="Historical Fiction"),
        ]
        session.add_all(categories)
        session.commit()
        print(f"   ✓ Added {len(categories)} categories")
        
        # ============================================
        # 4) ADD BOOKS
        # ============================================
        print("📝 Adding books...")
        books = [
            # Harry Potter series
            Book(isbn="978-0747532699", title="Harry Potter and the Philosopher's Stone", 
                 author_id=1, category_id=1, publication_year=1997, total_copies=5, available_copies=5),
            Book(isbn="978-0747538494", title="Harry Potter and the Chamber of Secrets", 
                 author_id=1, category_id=1, publication_year=1998, total_copies=5, available_copies=5),
            Book(isbn="978-0747542155", title="Harry Potter and the Prisoner of Azkaban", 
                 author_id=1, category_id=1, publication_year=1999, total_copies=5, available_copies=5),
            
            # Game of Thrones series
            Book(isbn="978-0553103540", title="A Game of Thrones", 
                 author_id=2, category_id=1, publication_year=1996, total_copies=4, available_copies=4),
            Book(isbn="978-0553108235", title="A Clash of Kings", 
                 author_id=2, category_id=1, publication_year=1998, total_copies=4, available_copies=4),
            
            # Tolkien
            Book(isbn="978-0544003415", title="The Fellowship of the Ring", 
                 author_id=3, category_id=1, publication_year=1954, total_copies=3, available_copies=3),
            Book(isbn="978-0544003422", title="The Two Towers", 
                 author_id=3, category_id=1, publication_year=1954, total_copies=3, available_copies=3),
            Book(isbn="978-0544003439", title="The Return of the King", 
                 author_id=3, category_id=1, publication_year=1955, total_copies=3, available_copies=3),
            
            # Stephen King
            Book(isbn="978-0451191730", title="The Shining", 
                 author_id=4, category_id=4, publication_year=1977, total_copies=3, available_copies=3),
            Book(isbn="978-0451192936", title="It", 
                 author_id=4, category_id=4, publication_year=1986, total_copies=3, available_copies=3),
            
            # Agatha Christie
            Book(isbn="978-0062693556", title="Murder on the Orient Express", 
                 author_id=5, category_id=3, publication_year=1934, total_copies=4, available_copies=4),
            Book(isbn="978-0062073577", title="And Then There Were None", 
                 author_id=5, category_id=3, publication_year=1939, total_copies=4, available_copies=4),
            
            # Isaac Asimov
            Book(isbn="978-0553293357", title="Foundation", 
                 author_id=6, category_id=2, publication_year=1951, total_copies=3, available_copies=3),
            
            # Margaret Atwood
            Book(isbn="978-0385490818", title="The Handmaid's Tale", 
                 author_id=7, category_id=6, publication_year=1985, total_copies=3, available_copies=3),
            
            # Haruki Murakami
            Book(isbn="978-0099448051", title="Norwegian Wood", 
                 author_id=8, category_id=6, publication_year=1987, total_copies=3, available_copies=3),
        ]
        session.add_all(books)
        session.commit()
        print(f"   ✓ Added {len(books)} books")
        
        # ============================================
        # 5) ADD ISSUE RECORDS
        # ============================================
        print("📝 Adding issue records...")
        now = datetime.now()
        
        issue_records = [
            # User 3 (John Doe) - Multiple issues in different states
            IssueRecord(
                user_id=3, book_id=1, 
                issued_at=now - timedelta(days=20),
                due_date=now - timedelta(days=6),
                status=IssueStatus.APPROVED,  # Approved but overdue
                returned_at=None
            ),
            IssueRecord(
                user_id=3, book_id=4,
                issued_at=now - timedelta(days=10),
                due_date=now + timedelta(days=4),
                status=IssueStatus.APPROVED,  # Approved, due soon
                returned_at=None
            ),
            IssueRecord(
                user_id=3, book_id=6,
                issued_at=now - timedelta(days=5),
                due_date=now + timedelta(days=9),
                status=IssueStatus.APPROVED,
                returned_at=None
            ),
            
            # User 4 (Jane Smith) - Issues in different states
            IssueRecord(
                user_id=4, book_id=2,
                issued_at=now - timedelta(days=12),
                due_date=now - timedelta(days=2),
                status=IssueStatus.RETURN_REQUESTED,  # Return requested
                returned_at=None
            ),
            IssueRecord(
                user_id=4, book_id=7,
                issued_at=now - timedelta(days=3),
                due_date=now + timedelta(days=11),
                status=IssueStatus.APPROVED,
                returned_at=None
            ),
            
            # User 5 (Bob Wilson) - Pending approval
            IssueRecord(
                user_id=5, book_id=3,
                issued_at=now - timedelta(hours=2),
                due_date=now + timedelta(days=14),
                status=IssueStatus.PENDING,  # Waiting for librarian approval
                returned_at=None
            ),
            
            # User 6 (Alice Johnson) - Has returned books
            IssueRecord(
                user_id=6, book_id=8,
                issued_at=now - timedelta(days=25),
                due_date=now - timedelta(days=11),
                status=IssueStatus.RETURNED,
                returned_at=now - timedelta(days=5),
                late_days=10,
                fine_amount=100.0
            ),
            IssueRecord(
                user_id=6, book_id=9,
                issued_at=now - timedelta(days=8),
                due_date=now + timedelta(days=6),
                status=IssueStatus.APPROVED,
                returned_at=None
            ),
            
            # User 7 (Charlie Brown) - Multiple issues
            IssueRecord(
                user_id=7, book_id=10,
                issued_at=now - timedelta(days=4),
                due_date=now + timedelta(days=10),
                status=IssueStatus.APPROVED,
                returned_at=None
            ),
            IssueRecord(
                user_id=7, book_id=11,
                issued_at=now - timedelta(days=30),
                due_date=now - timedelta(days=16),
                status=IssueStatus.RETURNED,
                returned_at=now - timedelta(days=15),
                late_days=15,
                fine_amount=150.0
            ),
            
            # User 8 (Diana Prince) - Recently issued
            IssueRecord(
                user_id=8, book_id=12,
                issued_at=now - timedelta(hours=6),
                due_date=now + timedelta(days=14),
                status=IssueStatus.APPROVED,
                returned_at=None
            ),
            IssueRecord(
                user_id=8, book_id=13,
                issued_at=now - timedelta(days=1),
                due_date=now + timedelta(days=13),
                status=IssueStatus.APPROVED,
                returned_at=None
            ),
        ]
        session.add_all(issue_records)
        session.commit()
        print(f"   ✓ Added {len(issue_records)} issue records")
        
        # ============================================
        # 6) ADD FINES
        # ============================================
        print("📝 Adding user fines...")
        fines = [
            UserFine(
                issue_id=7, user_id=6,
                fine_type=FineType.LATE_RETURN,
                fine_amount=100.0,
                is_paid=False
            ),
            UserFine(
                issue_id=10, user_id=7,
                fine_type=FineType.LATE_RETURN,
                fine_amount=150.0,
                is_paid=True,
                paid_at=now - timedelta(days=14)
            ),
        ]
        session.add_all(fines)
        session.commit()
        print(f"   ✓ Added {len(fines)} fines")
        
        # ============================================
        # 7) ADD NOTIFICATIONS
        # ============================================
        print("📝 Adding notifications...")
        notifications = [
            Notification(
                user_id=3,
                message="Your book 'Harry Potter and the Philosopher's Stone' is overdue by 6 days. Please return it to avoid fines.",
                notification_type=NotificationType.FINE_NOTICE
            ),
            Notification(
                user_id=4,
                message="Your book 'Harry Potter and the Chamber of Secrets' return is pending librarian approval.",
                notification_type=NotificationType.REMINDER
            ),
            Notification(
                user_id=5,
                message="Your book issue request for 'Harry Potter and the Prisoner of Azkaban' is waiting for librarian approval.",
                notification_type=NotificationType.SYSTEM
            ),
            Notification(
                user_id=6,
                message="You have an unpaid fine of Rs100.00 for late return of a book.",
                notification_type=NotificationType.FINE_NOTICE
            ),
            Notification(
                user_id=7,
                message="Your book 'And Then There Were None' is due in 10 days.",
                notification_type=NotificationType.REMINDER
            ),
        ]
        session.add_all(notifications)
        session.commit()
        print(f"   ✓ Added {len(notifications)} notifications")
        
        # Update book availability based on issued books
        print("📝 Updating book availability...")
        books_to_update = {}
        for record in issue_records:
            if record.status in [IssueStatus.PENDING, IssueStatus.APPROVED, IssueStatus.RETURN_REQUESTED]:
                if record.book_id not in books_to_update:
                    books_to_update[record.book_id] = 0
                books_to_update[record.book_id] += 1
        
        for book_id, borrowed_count in books_to_update.items():
            book = session.query(Book).filter_by(book_id=book_id).first()
            if book:
                book.available_copies = max(0, book.total_copies - borrowed_count)
        
        session.commit()
        print(f"   ✓ Updated availability for {len(books_to_update)} books")
        
        session.close()
        print("\n" + "="*50)
        print("✅ DATABASE SEEDING COMPLETE!")
        print("="*50)
        print("\n📊 Summary:")
        print(f"   • Users: {len(users)} (1 Admin, 1 Librarian, 6 Members)")
        print(f"   • Authors: {len(authors)}")
        print(f"   • Categories: {len(categories)}")
        print(f"   • Books: {len(books)}")
        print(f"   • Issue Records: {len(issue_records)}")
        print(f"   • Fines: {len(fines)}")
        print(f"   • Notifications: {len(notifications)}")
        print("\n🎯 Issue Status Distribution:")
        print(f"   • PENDING: 1 (waiting for approval)")
        print(f"   • APPROVED: 8 (active issues)")
        print(f"   • RETURN_REQUESTED: 1 (return pending)")
        print(f"   • RETURNED: 2 (completed issues)")
        print("\n🔐 Test Credentials:")
        print("   Admin:     admin@library.com")
        print("   Librarian: librarian@library.com")
        print("   Members:   john@example.com through diana@example.com")
        print("\n✨ Ready to test all features!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = seed_database()
    sys.exit(0 if success else 1)
