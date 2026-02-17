import httpx
from typing import Optional, Dict, Any, List
from github import Github, GithubException
from app.config import settings
import logging

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"
GITHUB_OAUTH_URL = "https://github.com/login/oauth"


def get_github_oauth_url(state: str) -> str:
    """Generate GitHub OAuth authorization URL."""
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "repo,read:user,user:email,admin:repo_hook",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GITHUB_OAUTH_URL}/authorize?{query}"


async def exchange_code_for_token(code: str) -> Optional[str]:
    """Exchange OAuth code for access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_OAUTH_URL}/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        logger.error(f"Failed to exchange code: {response.text}")
        return None


async def get_github_user(access_token: str) -> Optional[Dict[str, Any]]:
    """Fetch authenticated GitHub user information."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        if response.status_code == 200:
            return response.json()
        logger.error(f"Failed to get GitHub user: {response.status_code}")
        return None


async def get_github_user_emails(access_token: str) -> List[Dict[str, Any]]:
    """Fetch authenticated GitHub user emails."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        if response.status_code == 200:
            return response.json()
        return []


def get_github_client(access_token: str) -> Github:
    """Create an authenticated PyGithub client."""
    return Github(access_token)


async def get_pr_diff(access_token: str, repo_full_name: str, pr_number: int) -> Optional[str]:
    """Fetch the diff for a pull request."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/repos/{repo_full_name}/pulls/{pr_number}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.diff",
            },
        )
        if response.status_code == 200:
            return response.text
        logger.error(f"Failed to get PR diff: {response.status_code}")
        return None


async def get_pr_files(access_token: str, repo_full_name: str, pr_number: int) -> List[Dict[str, Any]]:
    """Fetch the list of changed files in a PR."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/repos/{repo_full_name}/pulls/{pr_number}/files",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        if response.status_code == 200:
            return response.json()
        return []


async def create_webhook(
    access_token: str,
    repo_full_name: str,
    webhook_url: str,
    secret: str
) -> Optional[int]:
    """Create a webhook for a GitHub repository."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_API_URL}/repos/{repo_full_name}/hooks",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={
                "name": "web",
                "active": True,
                "events": ["pull_request", "push"],
                "config": {
                    "url": webhook_url,
                    "content_type": "json",
                    "secret": secret,
                    "insecure_ssl": "0",
                },
            },
        )
        if response.status_code == 201:
            return response.json().get("id")
        logger.error(f"Failed to create webhook: {response.text}")
        return None


async def post_pr_comment(
    access_token: str,
    repo_full_name: str,
    pr_number: int,
    comment: str
) -> bool:
    """Post a comment on a GitHub PR."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_API_URL}/repos/{repo_full_name}/issues/{pr_number}/comments",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={"body": comment},
        )
        return response.status_code == 201


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    import hmac
    import hashlib
    expected = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
