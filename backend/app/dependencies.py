from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.user import User
from app.core.security import decode_access_token
from app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _extract_token(request: Request, header_token: str | None) -> str:
    token = header_token or request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return token


async def get_current_tenant(
    request: Request,
    header_token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> str:
    """
    Extract tenant context from JWT and set PostgreSQL session variable for RLS.

    This dependency sets the app.current_tenant_id session variable that PostgreSQL
    Row-Level Security policies use to filter data. Uses SET LOCAL to scope the
    variable to the current transaction only.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        tenant_id as string

    Raises:
        HTTPException: 401 if token invalid or tenant_id missing
    """
    token = _extract_token(request, header_token)
    payload = decode_access_token(token)
    tenant_id = payload.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing tenant_id",
        )

    await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))

    return tenant_id


async def get_current_user(
    request: Request,
    header_token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract current user from JWT token.

    Does NOT call get_current_tenant - tenant context must be set separately
    if needed. Some routes (like login) don't need tenant context.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User instance

    Raises:
        HTTPException: 401 if user not found, 403 if email not verified
    """
    token = _extract_token(request, header_token)
    payload = decode_access_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user_id",
        )

    # Query user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    return user
