"""
utils.py

Role: Provide required helper functions for library policies, fine calculation,
due date computation, and lost book penalties.
All functions are used by services/library.py.
"""

from datetime import datetime, timedelta

# ---------------------------
# Fine Calculation
# ---------------------------
def calculate_fine(late_days: int, fine_per_day: float) -> float:
    """
    Calculate fine based on late days and per-day fine.

    Args:
        late_days (int): Number of days overdue
        fine_per_day (float): Fine per day

    Returns:
        float: Total fine
    """
    if late_days <= 0:
        return 0.0
    return late_days * fine_per_day

# ---------------------------
# Lost Book Penalty
# ---------------------------
def compute_lost_penalty(issue_record, policy) -> float:
    """
    Calculate fine when a book is lost.

    Args:
        issue_record: IssueRecord object
        policy: LibraryPolicies object

    Returns:
        float: Lost book penalty
    """
    # Base penalty = 2x total fine for a late book
    return max(issue_record.fine_amount, 0) * policy.lost_book_penalty_multiplier

# ---------------------------
# Due Date Computation
# ---------------------------
def compute_due_date(issue_date: datetime, max_days: int) -> datetime:
    """
    Compute the due date for a borrowed book.

    Args:
        issue_date (datetime): Date of issue
        max_days (int): Max issue days from policy

    Returns:
        datetime: Calculated due date
    """
    return issue_date + timedelta(days=max_days)
