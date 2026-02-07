from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class PRStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    merged = "merged"
    draft = "draft"


class AIStatus(str, enum.Enum):
    pending = "pending"
    analyzing = "analyzing"
    completed = "completed"
    failed = "failed"


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    pr_number = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=True)
    author = Column(String(255), nullable=False)
    author_avatar = Column(Text, nullable=True)
    base_branch = Column(String(255), nullable=False)
    head_branch = Column(String(255), nullable=False)
    status = Column(Enum(PRStatus), default=PRStatus.open, nullable=False)
    ai_status = Column(Enum(AIStatus), default=AIStatus.pending, nullable=False)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    changed_files = Column(Integer, default=0)
    quality_score = Column(Float, nullable=True)
    security_score = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)
    pr_url = Column(Text, nullable=True)
    diff_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    pr_created_at = Column(DateTime(timezone=True), nullable=True)
    pr_merged_at = Column(DateTime(timezone=True), nullable=True)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    repository = relationship("Repository", back_populates="pull_requests")
    analyses = relationship("Analysis", back_populates="pull_request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PullRequest(id={self.id}, pr_number={self.pr_number}, title={self.title[:30]})>"
