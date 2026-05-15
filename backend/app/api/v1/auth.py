from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import jwt

from app.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    VerifyEmailRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    MessageResponse,
)
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.token import VerificationToken, PasswordResetToken
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.tasks.email import send_verification_email, send_password_reset_email
from app.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register new user and create tenant.

    Creates a new tenant with the company name and a new admin user.
    User account is inactive until email is verified.
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create tenant
    tenant = Tenant(name=request.company_name)
    db.add(tenant)
    await db.flush()  # Get tenant.id

    # Create admin user
    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        tenant_id=tenant.id,
        role=UserRole.ADMIN,
        is_active=False,  # Will be activated after email verification
    )
    db.add(user)
    await db.flush()  # Get user.id

    # Create verification token
    verification_token = VerificationToken.create_for_user(user.id)
    db.add(verification_token)
    await db.commit()

    # Send verification email (async via Celery)
    send_verification_email.delay(user.email, verification_token.token)

    return MessageResponse(message="Verification email sent")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(request: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify user email address with token.

    Activates the user account if token is valid and not expired.
    """
    # Query verification token
    result = await db.execute(
        select(VerificationToken).where(VerificationToken.token == request.token)
    )
    token = result.scalar_one_or_none()

    if not token or token.expires_at < datetime.utcnow():
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
async def login(
    response: Response,
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.

    Returns JWT tokens in httpOnly cookies.
    """
    # Query user by email (no tenant filter - login happens before tenant context)
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Verify password
    if not verify_password(request.password, user.hashed_password):
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
    refresh_token = create_refresh_token(str(user.id))

    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=15 * 60,  # 15 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return MessageResponse(message="Login successful")


@router.post("/refresh", response_model=MessageResponse)
async def refresh(
    response: Response,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token from cookie.

    Returns new access token in httpOnly cookie.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    # Decode refresh token
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Get user
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Create new access token
    access_token = create_access_token(
        str(user.id), str(user.tenant_id), user.role.value
    )

    # Set new access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=15 * 60,  # 15 minutes
    )

    return MessageResponse(message="Token refreshed")


@router.post("/reset-password-request", response_model=MessageResponse)
async def reset_password_request(
    request: PasswordResetRequest, db: AsyncSession = Depends(get_db)
):
    """
    Request password reset email.

    Always returns success to avoid leaking user existence.
    """
    # Query user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if user:
        # Create password reset token
        reset_token = PasswordResetToken.create_for_user(user.id)
        db.add(reset_token)
        await db.commit()

        # Send reset email (async via Celery)
        send_password_reset_email.delay(user.email, reset_token.token)

    # Always return success (don't leak user existence)
    return MessageResponse(message="Password reset email sent if account exists")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: PasswordResetConfirm, db: AsyncSession = Depends(get_db)
):
    """
    Reset password with token.

    Changes user password if token is valid and not expired.
    """
    # Query password reset token
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == request.token)
    )
    token = result.scalar_one_or_none()

    if not token or token.expires_at < datetime.utcnow():
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
    user.hashed_password = hash_password(request.new_password)

    # Delete reset token
    await db.delete(token)
    await db.commit()

    return MessageResponse(message="Password reset successful")


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    """
    Logout user by clearing auth cookies.
    """
    response.set_cookie(key="access_token", value="", max_age=0)
    response.set_cookie(key="refresh_token", value="", max_age=0)

    return MessageResponse(message="Logged out")
