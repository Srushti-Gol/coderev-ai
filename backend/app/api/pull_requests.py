from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import logging

from app.database import get_db
from app.models.pull_request import PullRequest, PRStatus, AIStatus
from app.models.repository import Repository
from app.schemas.pull_request import PullRequestResponse
from app.core.security import get_current_user_id
from app.workers.tasks import analyze_pr

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[PullRequestResponse])
async def list_pull_requests(
    repo_id: Optional[int] = None,
    status: Optional[str] = None,
    ai_status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List pull requests across all user repositories or for a specific repo."""
    # Base query - join with repositories to filter by user
    query = (
        select(PullRequest)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(Repository.user_id == current_user_id)
    )

    if repo_id:
        query = query.where(PullRequest.repo_id == repo_id)
    if status:
        query = query.where(PullRequest.status == status)
    if ai_status:
        query = query.where(PullRequest.ai_status == ai_status)

    query = query.order_by(PullRequest.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{pr_id}", response_model=PullRequestResponse)
async def get_pull_request(
    pr_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific pull request."""
    result = await db.execute(
        select(PullRequest)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            PullRequest.id == pr_id,
            Repository.user_id == current_user_id
        )
    )
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")
    return pr


@router.post("/{pr_id}/analyze")
async def trigger_analysis(
    pr_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI analysis for a pull request."""
    result = await db.execute(
        select(PullRequest)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            PullRequest.id == pr_id,
            Repository.user_id == current_user_id
        )
    )
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    if pr.ai_status == AIStatus.analyzing:
        return {"message": "Analysis already in progress", "task_id": None}

    # Queue the analysis task
    task = analyze_pr.delay(pr_id)

    # Update status
    pr.ai_status = AIStatus.analyzing
    await db.commit()

    return {"message": "Analysis started", "task_id": task.id}


@router.get("/{pr_id}/sync")
async def sync_pull_request(
    pr_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Sync pull request status from GitHub."""
    result = await db.execute(
        select(PullRequest)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            PullRequest.id == pr_id,
            Repository.user_id == current_user_id
        )
    )
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    # Fetch latest from GitHub
    from app.models.user import User
    from app.core.github import get_github_client
    user_result = await db.execute(select(User).where(User.id == current_user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    repo_result = await db.execute(select(Repository).where(Repository.id == pr.repo_id))
    repo = repo_result.scalar_one_or_none()

    try:
        gh = get_github_client(user.access_token)
        gh_repo = gh.get_repo(repo.full_name)
        gh_pr = gh_repo.get_pull(pr.pr_number)

        pr.title = gh_pr.title
        pr.status = gh_pr.state
        pr.additions = gh_pr.additions
        pr.deletions = gh_pr.deletions
        pr.changed_files = gh_pr.changed_files
        if gh_pr.merged:
            pr.pr_merged_at = gh_pr.merged_at

        await db.commit()
        await db.refresh(pr)
    except Exception as e:
        logger.error(f"Failed to sync PR {pr_id}: {e}")

    return pr
