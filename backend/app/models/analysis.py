from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class AnalysisType(str, enum.Enum):
    security = "security"
    quality = "quality"
    performance = "performance"
    duplicate = "duplicate"
    debt = "debt"
    bug = "bug"
    readability = "readability"
    best_practice = "best_practice"
    test = "test"


class Severity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    pr_id = Column(Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)
    analysis_type = Column(Enum(AnalysisType), nullable=False)
    severity = Column(Enum(Severity), nullable=False, default=Severity.medium)
    file_path = Column(Text, nullable=True)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    message = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)
    code_snippet = Column(Text, nullable=True)
    suggested_code = Column(Text, nullable=True)
    rule_id = Column(String(100), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    pull_request = relationship("PullRequest", back_populates="analyses")

    def __repr__(self):
        return f"<Analysis(id={self.id}, type={self.analysis_type}, severity={self.severity})>"
