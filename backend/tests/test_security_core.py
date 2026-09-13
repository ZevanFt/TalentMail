"""JWT / 密码哈希核心路径测试"""
from datetime import timedelta

import pytest
from jose import jwt

from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)


class TestPasswordHash:
    def test_hash_and_verify(self):
        hashed = get_password_hash("S3curePass!")
        assert hashed != "S3curePass!"
        assert verify_password("S3curePass!", hashed) is True

    def test_wrong_password_rejected(self):
        hashed = get_password_hash("S3curePass!")
        assert verify_password("WrongPass!", hashed) is False

    def test_hashes_differ_for_same_password(self):
        a = get_password_hash("same")
        b = get_password_hash("same")
        assert a != b


class TestJwtTokens:
    def test_access_token_contains_type_and_sub(self):
        token = create_access_token(data={"sub": "user@example.com", "session_id": 99})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "user@example.com"
        assert payload["token_type"] == "access"
        assert payload["session_id"] == 99

    def test_refresh_token_type_is_refresh(self):
        token = create_refresh_token(data={"sub": "user@example.com"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["token_type"] == "refresh"

    def test_verify_access_token(self):
        token = create_access_token(
            data={"sub": "user@example.com", "session_id": 7},
            expires_delta=timedelta(minutes=5),
        )
        data = verify_token(token, expected_type="access")
        assert data is not None
        assert data.sub == "user@example.com"
        assert data.session_id == 7

    def test_refresh_token_not_accepted_as_access(self):
        token = create_refresh_token(data={"sub": "user@example.com"})
        assert verify_token(token, expected_type="access") is None

    def test_access_token_not_accepted_as_refresh(self):
        token = create_access_token(data={"sub": "user@example.com"})
        assert verify_token(token, expected_type="refresh") is None

    def test_garbage_token_returns_none(self):
        assert verify_token("not-a-jwt") is None

    def test_expired_token_returns_none(self):
        token = create_access_token(
            data={"sub": "user@example.com"},
            expires_delta=timedelta(seconds=-10),
        )
        assert verify_token(token, expected_type="access") is None
