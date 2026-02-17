from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import logging

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.core.security import (
    create_access_token,
    get_current_user_id,
    create_github_state_token,
    verify_github_state_token,
)
from app.core.github import (
    get_github_oauth_url,
    exchange_code_for_token,
    get_github_user,
    get_github_user_emails,
)
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/github")
async def github_login():
    """Redirect to GitHub OAuth authorization page."""
    state = create_github_state_token()
    oauth_url = get_github_oauth_url(state)
    return RedirectResponse(url=oauth_url)


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback."""
    if not verify_github_state_token(state):
        raise HTTPException(status_code=400, detail="Invalid state token")

    # Exchange code for access token
    access_token = await exchange_code_for_token(code)
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    # Fetch GitHub user info
    github_user = await get_github_user(access_token)
    if not github_user:
        raise HTTPException(status_code=400, detail="Failed to fetch GitHub user")

    # Get primary email if not in user data
    email = github_user.get("email")
    if not email:
        emails = await get_github_user_emails(access_token)
        primary_emails = [e for e in emails if e.get("primary")]
        if primary_emails:
            email = primary_emails[0].get("email")

    # Upsert user in database
    result = await db.execute(
        select(User).where(User.github_id == github_user["id"])
    )
    user = result.scalar_one_or_none()

    if user:
        user.github_login = github_user["login"]
        user.email = email
        user.name = github_user.get("name")
        user.avatar_url = github_user.get("avatar_url")
        user.access_token = access_token
    else:
        user = User(
            github_id=github_user["id"],
            github_login=github_user["login"],
            email=email,
            name=github_user.get("name"),
            avatar_url=github_user.get("avatar_url"),
            access_token=access_token,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    # Create JWT token
    jwt_token = create_access_token(
        data={"sub": str(user.id), "github_login": user.github_login},
        expires_delta=timedelta(minutes=settings.jwt_expire_minutes),
    )

    # Redirect to frontend with token
    frontend_url = f"{settings.frontend_url}/auth/callback?token={jwt_token}"
    return RedirectResponse(url=frontend_url)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the currently authenticated user."""
    result = await db.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/logout")
async def logout(current_user_id: int = Depends(get_current_user_id)):
    """Logout - client should discard the JWT token."""
    return {"message": "Successfully logged out"}
