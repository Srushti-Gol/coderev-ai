from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.pull_request import PRStatus, AIStatus


class PullRequestBase(BaseModel):
    pr_number: int
    title: str
    body: Optional[str] = None
    author: str
    author_avatar: Optional[str] = None
    base_branch: str
    head_branch: str


class PullRequestCreate(PullRequestBase):
    repo_id: int
    pr_url: Optional[str] = None
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    pr_created_at: Optional[datetime] = None


class PullRequestResponse(PullRequestBase):
    id: int
    repo_id: int
    status: PRStatus
    ai_status: AIStatus
    additions: int
    deletions: int
    changed_files: int
    quality_score: Optional[float] = None
    security_score: Optional[float] = None
    performance_score: Optional[float] = None
    pr_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    pr_created_at: Optional[datetime] = None
    pr_merged_at: Optional[datetime] = None
    analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
