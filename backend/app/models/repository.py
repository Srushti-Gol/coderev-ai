from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    github_repo_id = Column(BigInteger, unique=True, nullable=False, index=True)
    full_name = Column(String(500), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(String(100), nullable=True)
    is_private = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    webhook_id = Column(BigInteger, nullable=True)
    default_branch = Column(String(255), default="main")
    stars_count = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    open_prs_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="repositories")
    pull_requests = relationship("PullRequest", back_populates="repository", cascade="all, delete-orphan")
    technical_debts = relationship("TechnicalDebt", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository(id={self.id}, full_name={self.full_name})>"
