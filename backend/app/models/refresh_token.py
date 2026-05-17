from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from datetime import datetime, timedelta, timezone
import uuid
import hashlib
import secrets


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def create_for_user(user_id: uuid.UUID) -> tuple["RefreshToken", str]:
        raw_token = secrets.token_urlsafe(48)
        return RefreshToken(
            user_id=user_id,
            token_hash=RefreshToken.hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ), raw_token
