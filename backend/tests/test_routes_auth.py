"""Integration tests for auth route endpoints."""

import uuid
from unittest.mock import patch

from httpx import AsyncClient

from app.core.security import create_access_token
from app.schemas.user import User


class TestRegisterRoute:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "strongpass",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert "id" in data
        # Password must never appear in response
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": test_user.email, "password": "whatever"},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "pass123"},
        )
        assert response.status_code == 422

    async def test_register_missing_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "valid@example.com"},
        )
        assert response.status_code == 422

    async def test_register_disabled(self, client: AsyncClient):
        with patch("app.services.auth.get_settings") as mock_settings:
            mock_settings.return_value.allow_registration = False
            response = await client.post(
                "/api/v1/auth/register",
                json={"email": "new@example.com", "password": "strongpass"},
            )
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"]


class TestLoginRoute:
    async def test_login_success(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "testpassword"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "anything"},
        )
        assert response.status_code == 401

    async def test_login_inactive_user(self, client: AsyncClient, inactive_user: User):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "testpassword"},
        )
        assert response.status_code == 403


class TestMeRoute:
    async def test_me_authenticated(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == str(test_user.id)

    async def test_me_no_token(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    async def test_me_nonexistent_user_token(self, client: AsyncClient):
        """Token is valid but references a user ID that doesn't exist."""
        token = create_access_token(subject=str(uuid.uuid4()))
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_me_inactive_user_token(
        self, client: AsyncClient, inactive_user: User
    ):
        """Token is valid but the user is deactivated."""
        token = create_access_token(subject=str(inactive_user.id))
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
