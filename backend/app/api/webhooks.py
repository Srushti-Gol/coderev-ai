from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import json
import logging
import hashlib
import hmac

from app.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.pull_request import PullRequest, PRStatus, AIStatus
from app.models.user import User
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None),
):
    """Handle GitHub webhook events."""
    payload_bytes = await request.body()

    # Verify webhook signature
    if settings.github_webhook_secret and x_hub_signature_256:
        if not verify_github_signature(
            payload_bytes,
            x_hub_signature_256,
            settings.github_webhook_secret
        ):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = x_github_event
    logger.info(f"Received GitHub webhook event: {event_type}")

    if event_type == "pull_request":
        await handle_pull_request_event(payload)
    elif event_type == "ping":
        return {"message": "pong"}
    else:
        logger.debug(f"Unhandled event type: {event_type}")

    return {"message": "OK"}


async def handle_pull_request_event(payload: dict):
    """Handle pull_request webhook events."""
    action = payload.get("action")
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})

    if action not in ["opened", "synchronize", "reopened"]:
        logger.debug(f"Skipping PR action: {action}")
        return

    github_repo_id = repo_data.get("id")

    async with AsyncSessionLocal() as db:
        # Find repository in our database
        repo_result = await db.execute(
            select(Repository).where(Repository.github_repo_id == github_repo_id)
        )
        repo = repo_result.scalar_one_or_none()
        if not repo or not repo.is_active:
            logger.debug(f"Repository {github_repo_id} not tracked or inactive")
            return

        pr_number = pr_data.get("number")

        # Check if PR exists
        pr_result = await db.execute(
            select(PullRequest).where(
                PullRequest.repo_id == repo.id,
                PullRequest.pr_number == pr_number
            )
        )
        pr = pr_result.scalar_one_or_none()

        if pr:
            # Update existing PR
            pr.title = pr_data.get("title", pr.title)
            pr.status = pr_data.get("state", pr.status)
            pr.additions = pr_data.get("additions", pr.additions)
            pr.deletions = pr_data.get("deletions", pr.deletions)
            pr.changed_files = pr_data.get("changed_files", pr.changed_files)
            pr.ai_status = AIStatus.pending
        else:
            # Create new PR
            pr = PullRequest(
                repo_id=repo.id,
                pr_number=pr_number,
                title=pr_data.get("title", ""),
                body=pr_data.get("body"),
                author=pr_data.get("user", {}).get("login", ""),
                author_avatar=pr_data.get("user", {}).get("avatar_url"),
                base_branch=pr_data.get("base", {}).get("ref", "main"),
                head_branch=pr_data.get("head", {}).get("ref", ""),
                status=PRStatus.open,
                ai_status=AIStatus.pending,
                additions=pr_data.get("additions", 0),
                deletions=pr_data.get("deletions", 0),
                changed_files=pr_data.get("changed_files", 0),
                pr_url=pr_data.get("html_url"),
            )
            db.add(pr)

        await db.commit()
        await db.refresh(pr)

        # Queue analysis task
        from app.workers.tasks import analyze_pr
        analyze_pr.delay(pr.id)
        pr.ai_status = AIStatus.analyzing
        await db.commit()

        logger.info(f"Queued analysis for PR #{pr_number} in {repo.full_name}")
