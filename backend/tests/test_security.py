"""Unit tests for password hashing and JWT helpers."""

from jose import jwt

from app.config import get_settings
from app.security import (
    COOKIE_NAME,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

SETTINGS = get_settings()


class TestPasswordHashing:
    def test_roundtrip(self):
        digest = hash_password("hunter2")
        assert verify_password("hunter2", digest)

    def test_wrong_password_fails(self):
        digest = hash_password("hunter2")
        assert not verify_password("hunter3", digest)

    def test_hashes_are_salted(self):
        assert hash_password("same") != hash_password("same")

    def test_empty_password_hashes(self):
        digest = hash_password("")
        assert verify_password("", digest)


class TestJWTs:
    def test_roundtrip(self):
        token = create_access_token("admin")
        assert decode_access_token(token) == "admin"

    def test_garbage_token_is_none(self):
        assert decode_access_token("not.a.jwt") is None

    def test_expired_token_is_none(self):
        from datetime import datetime, timedelta, timezone

        token = jwt.encode(
            {"sub": "admin", "exp": datetime.now(timezone.utc) - timedelta(minutes=5)},
            SETTINGS.jwt_secret,
            algorithm=SETTINGS.jwt_algorithm,
        )
        assert decode_access_token(token) is None

    def test_wrong_secret_is_none(self):
        token = jwt.encode({"sub": "admin"}, "a-different-secret", algorithm=SETTINGS.jwt_algorithm)
        assert decode_access_token(token) is None

    def test_cookie_name(self):
        assert COOKIE_NAME == "admin_session"