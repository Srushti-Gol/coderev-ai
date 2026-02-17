from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import logging

from app.database import get_db
from app.models.repository import Repository
from app.models.user import User
from app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryUpdate
from app.core.security import get_current_user_id
from app.core.github import get_github_client, create_webhook
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List repositories for the current user."""
    query = select(Repository).where(Repository.user_id == current_user_id)
    if search:
        query = query.where(Repository.full_name.ilike(f"%{search}%"))
    query = query.order_by(Repository.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific repository."""
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.user_id == current_user_id
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.post("/sync", response_model=List[RepositoryResponse])
async def sync_repositories(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Sync repositories from GitHub."""
    # Get user and their access token
    result = await db.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()
    if not user or not user.access_token:
        raise HTTPException(status_code=401, detail="GitHub access token not found")

    # Fetch repos from GitHub
    gh = get_github_client(user.access_token)
    github_repos = list(gh.get_user().get_repos(type="owner", sort="updated"))[:50]

    synced_repos = []
    for gh_repo in github_repos:
        # Check if repo already exists
        existing = await db.execute(
            select(Repository).where(Repository.github_repo_id == gh_repo.id)
        )
        repo = existing.scalar_one_or_none()

        if repo:
            repo.full_name = gh_repo.full_name
            repo.name = gh_repo.name
            repo.description = gh_repo.description
            repo.language = gh_repo.language
            repo.stars_count = gh_repo.stargazers_count
            repo.forks_count = gh_repo.forks_count
            repo.default_branch = gh_repo.default_branch
        else:
            repo = Repository(
                user_id=current_user_id,
                github_repo_id=gh_repo.id,
                full_name=gh_repo.full_name,
                name=gh_repo.name,
                description=gh_repo.description,
                language=gh_repo.language,
                is_private=gh_repo.private,
                stars_count=gh_repo.stargazers_count,
                forks_count=gh_repo.forks_count,
                default_branch=gh_repo.default_branch,
            )
            db.add(repo)

        synced_repos.append(repo)

    await db.commit()
    for repo in synced_repos:
        await db.refresh(repo)

    return synced_repos


@router.post("/{repo_id}/activate")
async def activate_repository(
    repo_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Activate a repository for AI code review and set up webhook."""
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.user_id == current_user_id
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Get user access token
    user_result = await db.execute(select(User).where(User.id == current_user_id))
    user = user_result.scalar_one_or_none()

    # Set up webhook
    webhook_url = f"{settings.frontend_url.replace('3000', '8000')}/webhooks/github"
    webhook_id = await create_webhook(
        user.access_token,
        repo.full_name,
        webhook_url,
        settings.github_webhook_secret,
    )

    repo.is_active = True
    if webhook_id:
        repo.webhook_id = webhook_id

    await db.commit()
    return {"message": "Repository activated", "webhook_id": webhook_id}


@router.post("/{repo_id}/deactivate")
async def deactivate_repository(
    repo_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a repository."""
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.user_id == current_user_id
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo.is_active = False
    await db.commit()
    return {"message": "Repository deactivated"}


@router.delete("/{repo_id}")
async def delete_repository(
    repo_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a repository from tracking."""
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.user_id == current_user_id
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    await db.delete(repo)
    await db.commit()
    return {"message": "Repository deleted"}
