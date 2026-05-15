from fastapi import Depends, HTTPException, status
from app.dependencies import get_current_user
from app.models.user import User, UserRole


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require user to have admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        User instance if admin

    Raises:
        HTTPException: 403 if not admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_active(current_user: User = Depends(get_current_user)) -> User:
    """
    Require user account to be active (email verified).

    Args:
        current_user: Current authenticated user

    Returns:
        User instance if active

    Raises:
        HTTPException: 403 if not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    return current_user
