"""Unit tests for password hashing and JWT utilities."""

import uuid

from jose import JWTError, jwt

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.settings import get_settings


class TestPasswordHashing:
    def test_hash_returns_bcrypt_string(self):
        hashed = hash_password("mypassword")
        assert hashed.startswith("$2b$")

    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"

    def test_verify_correct_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_input(self):
        h1 = hash_password("mypassword")
        h2 = hash_password("mypassword")
        assert h1 != h2  # salt differs


class TestJWT:
    def test_create_and_decode_token(self):
        subject = str(uuid.uuid4())
        token = create_access_token(subject=subject)
        payload = decode_access_token(token)
        assert payload["sub"] == subject
        assert "exp" in payload

    def test_token_with_extra_claims(self):
        token = create_access_token(subject="user-1", extra={"role": "admin"})
        payload = decode_access_token(token)
        assert payload["sub"] == "user-1"
        assert payload["role"] == "admin"

    def test_decode_invalid_token_raises(self):
        try:
            decode_access_token("not-a-valid-token")
            msg = "Expected JWTError"
            raise AssertionError(msg)
        except JWTError:
            pass

    def test_decode_tampered_token_raises(self):
        token = create_access_token(subject="user-1")
        settings = get_settings()
        # Re-encode with wrong secret
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        tampered = jwt.encode(payload, "wrong-secret", algorithm=settings.jwt_algorithm)
        try:
            decode_access_token(tampered)
            msg = "Expected JWTError"
            raise AssertionError(msg)
        except JWTError:
            pass
