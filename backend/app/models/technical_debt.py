from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class TechnicalDebt(Base):
    __tablename__ = "technical_debts"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    pr_id = Column(Integer, ForeignKey("pull_requests.id", ondelete="SET NULL"), nullable=True)

    # Debt scores (0-100 scale, higher is worse)
    overall_score = Column(Float, nullable=False, default=0.0)
    security_score = Column(Float, nullable=False, default=0.0)
    quality_score = Column(Float, nullable=False, default=0.0)
    performance_score = Column(Float, nullable=False, default=0.0)
    maintainability_score = Column(Float, nullable=False, default=0.0)
    test_coverage_score = Column(Float, nullable=False, default=0.0)

    # Raw metrics
    cyclomatic_complexity_avg = Column(Float, nullable=True)
    duplicate_code_percentage = Column(Float, nullable=True)
    long_functions_count = Column(Integer, nullable=True)
    deep_nesting_count = Column(Integer, nullable=True)
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)

    # Breakdown by category stored as JSON
    breakdown = Column(JSON, nullable=True)

    # Version/release tag for comparison
    version_tag = Column(String(100), nullable=True)
    commit_sha = Column(String(40), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="technical_debts")

    def __repr__(self):
        return f"<TechnicalDebt(id={self.id}, repo_id={self.repo_id}, score={self.overall_score})>"
