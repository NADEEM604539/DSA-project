"""
auth.py

Authentication module for role-based access control.
- Backend is API-first: Frontend handles Clerk authentication
- User creation/login is handled via REST API calls from frontend
- Backend validates user_id passed in requests

User authentication flow:
1. Frontend authenticates user with Clerk
2. Frontend gets user data from Clerk
3. Frontend calls POST /admin/users with user data (user_id, email, role)
4. Backend stores user in database
5. Frontend includes user_id in subsequent API calls
"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import User


def get_current_user(db: Session = Depends(get_db)) -> User:
    """
    Get the current user from the request.
    
    NOTE: This is a helper function for endpoints that need user context.
    Most endpoints receive user_id directly in request body from frontend.
    """
    # Default user for compatibility - endpoints typically receive user_id in request
    default_user_id = "admin001"
    
    user = db.query(User).filter(User.user_id == default_user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found or not authenticated")
    
    return user
