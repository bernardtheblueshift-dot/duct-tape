from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TenantMixin, TimestampMixin
from app.models.user import UserRole
from datetime import datetime, timedelta
import uuid
import secrets


class VerificationToken(Base, TimestampMixin):
    __tablename__ = "verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    @staticmethod
    def generate_token() -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_for_user(user_id: uuid.UUID) -> "VerificationToken":
        """Create verification token with 24-hour expiry"""
        return VerificationToken(
            user_id=user_id,
            token=VerificationToken.generate_token(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )


class PasswordResetToken(Base, TimestampMixin):
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    @staticmethod
    def create_for_user(user_id: uuid.UUID) -> "PasswordResetToken":
        """Create password reset token with 1-hour expiry"""
        return PasswordResetToken(
            user_id=user_id,
            token=secrets.token_urlsafe(32),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )


class InvitationToken(Base, TenantMixin, TimestampMixin):
    __tablename__ = "invitation_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, index=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CREW)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # tenant_id from TenantMixin - invitee joins this tenant

    @staticmethod
    def create(
        email: str,
        tenant_id: uuid.UUID,
        invited_by: uuid.UUID,
        role: UserRole = UserRole.CREW,
    ) -> "InvitationToken":
        """Create invitation token with 7-day expiry"""
        return InvitationToken(
            email=email,
            tenant_id=tenant_id,
            invited_by=invited_by,
            role=role,
            token=secrets.token_urlsafe(32),
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
