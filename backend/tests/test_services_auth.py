"""Unit tests for the authentication service layer."""

from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserCreate
from app.schemas.user import User
from app.services.auth import AuthError, authenticate_user, register_user


class TestRegisterUser:
    async def test_register_creates_user(self, session: AsyncSession):
        data = UserCreate(email="new@example.com", password="strongpass", full_name="New User")
        user = await register_user(session, data)
        assert user.email == "new@example.com"
        assert user.full_name == "New User"
        assert user.id is not None
        assert user.is_active is True

    async def test_register_hashes_password(self, session: AsyncSession):
        data = UserCreate(email="hash@example.com", password="plaintext")
        user = await register_user(session, data)
        assert user.hashed_password != "plaintext"
        assert user.hashed_password.startswith("$2b$")

    async def test_register_duplicate_email_raises(self, session: AsyncSession, test_user: User):
        data = UserCreate(email=test_user.email, password="another")
        with pytest.raises(AuthError, match="already exists") as exc_info:
            await register_user(session, data)
        assert exc_info.value.status_code == 409

    async def test_register_disabled_raises(self, session: AsyncSession):
        data = UserCreate(email="blocked@example.com", password="strongpass")
        with patch(
            "app.services.auth.get_settings"
        ) as mock_settings:
            mock_settings.return_value.allow_registration = False
            with pytest.raises(AuthError, match="disabled") as exc_info:
                await register_user(session, data)
            assert exc_info.value.status_code == 403

    async def test_register_bypass_when_disabled(self, session: AsyncSession):
        """bypass_registration_check=True allows creation even when disabled."""
        data = UserCreate(email="bypassed@example.com", password="strongpass")
        with patch("app.services.auth.get_settings") as mock_settings:
            mock_settings.return_value.allow_registration = False
            user = await register_user(
                session, data, bypass_registration_check=True
            )
        assert user.email == "bypassed@example.com"


class TestAuthenticateUser:
    async def test_authenticate_valid_credentials(
        self, session: AsyncSession, test_user: User
    ):
        user = await authenticate_user(session, "testuser@example.com", "testpassword")
        assert user.id == test_user.id

    async def test_authenticate_wrong_password(self, session: AsyncSession, test_user: User):
        with pytest.raises(AuthError, match="Invalid email or password") as exc_info:
            await authenticate_user(session, "testuser@example.com", "wrongpassword")
        assert exc_info.value.status_code == 401

    async def test_authenticate_nonexistent_email(self, session: AsyncSession):
        with pytest.raises(AuthError, match="Invalid email or password") as exc_info:
            await authenticate_user(session, "nobody@example.com", "anything")
        assert exc_info.value.status_code == 401

    async def test_authenticate_inactive_user(self, session: AsyncSession, inactive_user: User):
        with pytest.raises(AuthError, match="disabled") as exc_info:
            await authenticate_user(session, "inactive@example.com", "testpassword")
        assert exc_info.value.status_code == 403
