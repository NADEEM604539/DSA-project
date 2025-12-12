"""
Daily Fine Challan Update Service
Runs every day to update fine challans and track payment status
"""

from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from db import SessionLocal
from models import UserFine, IssueRecord
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FineScheduler")

scheduler = BackgroundScheduler()


def update_fine_status():
    """
    Daily task to:
    1. Check for overdue payment deadlines
    2. Update fine status
    3. Log payment reminders
    """
    db = SessionLocal()
    try:
        # Get all unpaid fines
        unpaid_fines = db.query(UserFine).filter(UserFine.is_paid == False).all()
        
        today = datetime.now().date()
        
        for fine in unpaid_fines:
            # Calculate payment deadline (7 days from creation)
            created_date = fine.created_at.date() if hasattr(fine.created_at, 'date') else fine.created_at
            payment_deadline = created_date + timedelta(days=7)
            
            # Check if overdue
            if today > payment_deadline:
                logger.warning(
                    f"Fine #{fine.fine_id} for user #{fine.user_id} "
                    f"is OVERDUE (${fine.fine_amount}) - Due: {payment_deadline}"
                )
            else:
                days_remaining = (payment_deadline - today).days
                if days_remaining <= 3:
                    logger.info(
                        f"Fine #{fine.fine_id} for user #{fine.user_id} "
                        f"due in {days_remaining} days (${fine.fine_amount})"
                    )
        
        logger.info(f"Daily fine status check completed. Checked {len(unpaid_fines)} unpaid fines.")
        
    except Exception as e:
        logger.error(f"Error in update_fine_status: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler"""
    if not scheduler.running:
        # Schedule daily at 00:00 (midnight)
        scheduler.add_job(
            update_fine_status,
            'cron',
            hour=0,
            minute=0,
            id='daily_fine_update',
            name='Daily Fine Challan Update',
            replace_existing=True
        )
        scheduler.start()
        logger.info("Fine update scheduler started. Running daily at 00:00")


def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Fine update scheduler stopped")
