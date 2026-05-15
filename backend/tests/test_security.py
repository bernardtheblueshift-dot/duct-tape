import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from app.config import settings
import jwt
from fastapi import HTTPException


def test_hash_password_returns_bcrypt_hash():
    hashed = hash_password("password123")
    assert hashed.startswith("$2b$"), f"Invalid bcrypt hash: {hashed}"


def test_verify_password_with_correct_password():
    hashed = hash_password("password123")
    assert verify_password("password123", hashed) is True


def test_verify_password_with_wrong_password():
    hashed = hash_password("password123")
    assert verify_password("wrong", hashed) is False


def test_create_access_token_includes_user_tenant_role():
    access = create_access_token("user123", "tenant456", "admin")
    payload = jwt.decode(access, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == "user123"
    assert payload["tenant_id"] == "tenant456"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_create_access_token_expires_in_15_minutes():
    import time

    before = time.time()
    access = create_access_token("user123", "tenant456", "admin")
    after = time.time()

    payload = jwt.decode(access, settings.SECRET_KEY, algorithms=["HS256"])
    exp = payload["exp"]

    # Should expire ~15 minutes (900 seconds) from now
    expected_min = before + 890  # Allow 10 sec margin
    expected_max = after + 910

    assert expected_min <= exp <= expected_max, f"Expiry {exp} not in 15-minute range"


def test_create_refresh_token_expires_in_7_days():
    import time

    before = time.time()
    refresh = create_refresh_token("user123")
    after = time.time()

    payload = jwt.decode(refresh, settings.SECRET_KEY, algorithms=["HS256"])
    exp = payload["exp"]

    # Should expire ~7 days (604800 seconds) from now
    expected_min = before + 604700  # Allow 100 sec margin
    expected_max = after + 604900

    assert expected_min <= exp <= expected_max, f"Expiry {exp} not in 7-day range"
    assert payload["type"] == "refresh"


def test_decode_access_token_extracts_payload():
    access = create_access_token("user123", "tenant456", "crew")
    payload = decode_access_token(access)
    assert payload["sub"] == "user123"
    assert payload["tenant_id"] == "tenant456"
    assert payload["role"] == "crew"


def test_decode_access_token_raises_on_expired_token():
    # Create a token that's already expired
    from datetime import datetime, timedelta

    expired_payload = {
        "sub": "user123",
        "tenant_id": "tenant456",
        "role": "admin",
        "type": "access",
        "exp": datetime.utcnow() - timedelta(minutes=10),  # Expired 10 minutes ago
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(expired_token)

    assert exc_info.value.status_code == 401


def test_decode_access_token_raises_on_invalid_signature():
    # Create token with wrong secret
    fake_token = jwt.encode(
        {"sub": "user123", "tenant_id": "tenant456", "role": "admin", "type": "access"},
        "wrong-secret",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(fake_token)

    assert exc_info.value.status_code == 401
