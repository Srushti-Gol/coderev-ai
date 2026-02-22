import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient

from app.main import app
from app.models.user import User
from app.core.security import create_access_token, verify_token


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication endpoints."""

    async def test_github_login_redirects(self, async_client: AsyncClient):
        """Test that /auth/github redirects to GitHub OAuth."""
        response = await async_client.get("/auth/github", follow_redirects=False)
        assert response.status_code in [302, 307]
        assert "github.com/login/oauth/authorize" in response.headers.get("location", "")

    async def test_get_me_requires_auth(self, async_client: AsyncClient):
        """Test that /auth/me requires authentication."""
        response = await async_client.get("/auth/me")
        assert response.status_code == 403  # No auth header

    async def test_get_me_with_valid_token(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test /auth/me with valid JWT token."""
        response = await async_client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["github_login"] == test_user.github_login
        assert data["id"] == test_user.id

    async def test_get_me_with_invalid_token(self, async_client: AsyncClient):
        """Test /auth/me with invalid JWT token."""
        response = await async_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    async def test_logout(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test logout endpoint."""
        response = await async_client.post("/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

    async def test_github_callback_invalid_state(self, async_client: AsyncClient):
        """Test GitHub callback with invalid state token."""
        response = await async_client.get(
            "/auth/github/callback?code=test_code&state=invalid_state",
            follow_redirects=False,
        )
        assert response.status_code == 400

    async def test_github_callback_success(self, async_client: AsyncClient):
        """Test successful GitHub OAuth callback."""
        from app.core.security import create_github_state_token

        state = create_github_state_token()

        with patch("app.api.auth.exchange_code_for_token", new_callable=AsyncMock) as mock_exchange:
            with patch("app.api.auth.get_github_user", new_callable=AsyncMock) as mock_user:
                with patch("app.api.auth.get_github_user_emails", new_callable=AsyncMock) as mock_emails:
                    mock_exchange.return_value = "github_access_token"
                    mock_user.return_value = {
                        "id": 99999,
                        "login": "newuser",
                        "email": "newuser@example.com",
                        "name": "New User",
                        "avatar_url": "https://github.com/newuser.png",
                    }
                    mock_emails.return_value = [{"email": "newuser@example.com", "primary": True}]

                    response = await async_client.get(
                        f"/auth/github/callback?code=valid_code&state={state}",
                        follow_redirects=False,
                    )
                    assert response.status_code in [302, 307]
                    assert "token=" in response.headers.get("location", "")


class TestSecurityUtils:
    """Test security utility functions."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        token = create_access_token({"sub": "1", "github_login": "testuser"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Test verification of a valid token."""
        token = create_access_token({"sub": "123"})
        payload = verify_token(token)
        assert payload["sub"] == "123"

    def test_verify_invalid_token(self):
        """Test that invalid tokens raise an error."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.string")
        assert exc_info.value.status_code == 401

    def test_token_contains_expiry(self):
        """Test that tokens contain expiry claim."""
        token = create_access_token({"sub": "1"})
        payload = verify_token(token)
        assert "exp" in payload
        assert "iat" in payload
