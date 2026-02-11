from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.analysis import AnalysisType, Severity


class AnalysisBase(BaseModel):
    analysis_type: AnalysisType
    severity: Severity
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    suggested_code: Optional[str] = None
    rule_id: Optional[str] = None


class AnalysisCreate(AnalysisBase):
    pr_id: int


class AnalysisResponse(AnalysisBase):
    id: int
    pr_id: int
    is_verified: bool
    is_dismissed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisSummary(BaseModel):
    total: int
    critical: int
    high: int
    medium: int
    low: int
    info: int
    by_type: dict
    quality_score: float
    security_score: float
    performance_score: float
