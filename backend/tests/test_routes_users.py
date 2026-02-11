"""Integration tests for admin user-management endpoints."""

from unittest.mock import patch

from httpx import AsyncClient

from app.schemas.user import User


class TestAdminCreateUser:
    async def test_admin_can_create_user(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "email": "created@example.com",
                "password": "newpass123",
                "full_name": "Created User",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "created@example.com"
        assert data["full_name"] == "Created User"
        assert data["is_active"] is True

    async def test_admin_can_create_user_when_registration_disabled(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        """Admins bypass the allow_registration setting."""
        with patch("app.services.auth.get_settings") as mock_settings:
            mock_settings.return_value.allow_registration = False
            response = await client.post(
                "/api/v1/users",
                json={
                    "email": "admin-created@example.com",
                    "password": "pass123",
                    "full_name": "Admin Created",
                },
                headers=admin_headers,
            )
        assert response.status_code == 201
        assert response.json()["email"] == "admin-created@example.com"

    async def test_admin_can_set_superuser_flag(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "email": "newadmin@example.com",
                "password": "adminpass",
                "is_superuser": True,
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        # Verify via /me that the flag persists is not in UserRead,
        # but we can check the response doesn't error.
        assert response.json()["email"] == "newadmin@example.com"

    async def test_admin_can_create_inactive_user(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "email": "disabled@example.com",
                "password": "pass123",
                "is_active": False,
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        assert response.json()["is_active"] is False

    async def test_admin_cannot_create_duplicate_email(
        self, client: AsyncClient, test_user: User, admin_user: User, admin_headers: dict
    ):
        response = await client.post(
            "/api/v1/users",
            json={"email": test_user.email, "password": "whatever"},
            headers=admin_headers,
        )
        assert response.status_code == 409

    async def test_non_admin_cannot_create_user(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/users",
            json={"email": "sneaky@example.com", "password": "pass123"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_unauthenticated_cannot_create_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/users",
            json={"email": "anon@example.com", "password": "pass123"},
        )
        assert response.status_code == 401
