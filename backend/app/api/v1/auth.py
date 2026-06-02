from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    VerifyEmailRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    MessageResponse,
)
from app.schemas.user import UserResponse
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.token import VerificationToken, PasswordResetToken
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from app.tasks.email import send_verification_email, send_password_reset_email
from app.config import settings
import logging

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=MessageResponse)
@limiter.limit("3/minute")
async def register(request: Request, register_data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register new user and create tenant.

    Creates a new tenant with the company name and a new admin user.
    User account is inactive until email is verified.
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == register_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return MessageResponse(message="If this email is available, a verification email will be sent")

    # Create tenant
    tenant = Tenant(name=register_data.company_name)
    db.add(tenant)
    await db.flush()  # Get tenant.id

    # Create admin user
    user = User(
        email=register_data.email,
        name=register_data.name,
        hashed_password=hash_password(register_data.password),
        tenant_id=tenant.id,
        role=UserRole.ADMIN,
        is_active=settings.DEBUG,  # Auto-activate in dev mode, require email verification in prod
    )
    db.add(user)
    await db.flush()  # Get user.id

    # Create verification token
    verification_token = VerificationToken.create_for_user(user.id)
    db.add(verification_token)
    await db.commit()

    # Send verification email (async via Celery)
    try:
        send_verification_email.delay(user.email, verification_token.token)
    except Exception as e:
        logging.getLogger(__name__).warning("Failed to queue email: %s", e)

    return MessageResponse(message="Verification email sent")


@router.post("/verify-email", response_model=MessageResponse)
@limiter.limit("5/minute")
async def verify_email(request: Request, verify_data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify user email address with token.

    Activates the user account if token is valid and not expired.
    """
    # Query verification token
    result = await db.execute(
        select(VerificationToken).where(VerificationToken.token == verify_data.token)
    )
    token = result.scalar_one_or_none()

    if not token or token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == token.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Activate user
    user.is_active = True

    # Delete verification token
    await db.delete(token)
    await db.commit()

    return MessageResponse(message="Email verified")


@router.post("/login", response_model=MessageResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.

    Returns JWT tokens in httpOnly cookies.
    """
    # Query user by email (no tenant filter - login happens before tenant context)
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Check if email verified
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    # Create tokens
    access_token = create_access_token(
        str(user.id), str(user.tenant_id), user.role.value
    )
    from app.models.refresh_token import RefreshToken
    refresh_obj, raw_refresh_token = RefreshToken.create_for_user(user.id)
    db.add(refresh_obj)
    await db.flush()

    # Set cookies (secure=False in dev so browsers accept over HTTP)
    _secure = not settings.DEBUG
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=_secure,
        samesite="lax",
        max_age=15 * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=_secure,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    return MessageResponse(message="Login successful")


@router.post("/refresh", response_model=MessageResponse)
@limiter.limit("10/minute")
async def refresh(
    request: Request,
    response: Response,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token from cookie.

    Rotates refresh token on each use for security.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    from app.models.refresh_token import RefreshToken

    token_hash = RefreshToken.hash_token(refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
        )
    )
    stored_token = result.scalar_one_or_none()

    if not stored_token or stored_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == stored_token.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Rotate: revoke old token, create new one
    stored_token.revoked = True
    new_refresh_obj, new_raw_token = RefreshToken.create_for_user(user.id)
    db.add(new_refresh_obj)

    access_token = create_access_token(
        str(user.id), str(user.tenant_id), user.role.value
    )

    _secure = not settings.DEBUG
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=_secure,
        samesite="lax",
        max_age=15 * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_raw_token,
        httponly=True,
        secure=_secure,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    await db.flush()

    return MessageResponse(message="Token refreshed")


@router.post("/reset-password-request", response_model=MessageResponse)
@limiter.limit("3/minute")
async def reset_password_request(
    request: Request, reset_data: PasswordResetRequest, db: AsyncSession = Depends(get_db)
):
    """
    Request password reset email.

    Always returns success to avoid leaking user existence.
    """
    # Query user by email
    result = await db.execute(select(User).where(User.email == reset_data.email))
    user = result.scalar_one_or_none()

    if user:
        # Invalidate previous reset tokens
        from sqlalchemy import delete as sql_delete
        await db.execute(sql_delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))

        # Create password reset token
        reset_token = PasswordResetToken.create_for_user(user.id)
        db.add(reset_token)
        await db.commit()

        # Send reset email (async via Celery)
        try:
            send_password_reset_email.delay(user.email, reset_token.token)
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to queue email: %s", e)

    # Always return success (don't leak user existence)
    return MessageResponse(message="Password reset email sent if account exists")


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def reset_password(
    request: Request, reset_confirm: PasswordResetConfirm, db: AsyncSession = Depends(get_db)
):
    """
    Reset password with token.

    Changes user password if token is valid and not expired.
    """
    # Query password reset token
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == reset_confirm.token)
    )
    token = result.scalar_one_or_none()

    if not token or token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == token.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update password
    user.hashed_password = hash_password(reset_confirm.new_password)

    # Delete reset token
    await db.delete(token)
    await db.commit()

    return MessageResponse(message="Password reset successful")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout user by clearing auth cookies and revoking refresh token.
    """
    if refresh_token:
        from app.models.refresh_token import RefreshToken
        token_hash = RefreshToken.hash_token(refresh_token)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        if stored:
            stored.revoked = True
            await db.flush()

    _secure = not settings.DEBUG
    response.set_cookie(key="access_token", value="", max_age=0, httponly=True, secure=_secure, samesite="lax")
    response.set_cookie(key="refresh_token", value="", max_age=0, httponly=True, secure=_secure, samesite="lax")

    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
async def get_me(
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user from access token cookie.
    Used by frontend to check auth state on page load.
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(access_token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


@router.get("/ws-token")
async def get_ws_token(
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a short-lived token for WebSocket authentication.
    WebSocket cannot use httpOnly cookies, so this endpoint
    returns the token value for the ws?token= query param.
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(access_token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    from app.core.security import create_ws_token
    ws_token = create_ws_token(str(user.id), str(user.tenant_id), user.role.value)
    return {"token": ws_token}
