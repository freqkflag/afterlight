"""Shared dependencies for the application."""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User

__all__ = ["get_db", "get_current_user", "get_current_active_user"]


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user
