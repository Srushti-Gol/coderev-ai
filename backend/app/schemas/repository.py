from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RepositoryBase(BaseModel):
    full_name: str
    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    is_private: bool = False


class RepositoryCreate(RepositoryBase):
    github_repo_id: int
    user_id: int
    default_branch: str = "main"
    stars_count: int = 0
    forks_count: int = 0


class RepositoryUpdate(BaseModel):
    description: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None
    webhook_id: Optional[int] = None
    stars_count: Optional[int] = None
    open_prs_count: Optional[int] = None


class RepositoryResponse(RepositoryBase):
    id: int
    user_id: int
    github_repo_id: int
    is_active: bool
    webhook_id: Optional[int] = None
    default_branch: str
    stars_count: int
    forks_count: int
    open_prs_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
