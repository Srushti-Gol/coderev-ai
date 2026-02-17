from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import logging

from app.database import get_db
from app.models.analysis import Analysis, AnalysisType, Severity
from app.models.pull_request import PullRequest
from app.models.repository import Repository
from app.schemas.analysis import AnalysisResponse, AnalysisSummary
from app.core.security import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/pr/{pr_id}", response_model=List[AnalysisResponse])
async def get_pr_analyses(
    pr_id: int,
    analysis_type: Optional[str] = None,
    severity: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all analysis findings for a pull request."""
    # Verify access
    pr_result = await db.execute(
        select(PullRequest)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            PullRequest.id == pr_id,
            Repository.user_id == current_user_id
        )
    )
    if not pr_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Pull request not found")

    query = select(Analysis).where(Analysis.pr_id == pr_id, Analysis.is_dismissed == False)

    if analysis_type:
        query = query.where(Analysis.analysis_type == analysis_type)
    if severity:
        query = query.where(Analysis.severity == severity)

    query = query.order_by(
        Analysis.severity.desc(),
        Analysis.created_at.desc()
    ).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/pr/{pr_id}/summary", response_model=AnalysisSummary)
async def get_pr_analysis_summary(
    pr_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get analysis summary for a pull request."""
    # Verify access
    pr_result = await db.execute(
        select(PullRequest)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            PullRequest.id == pr_id,
            Repository.user_id == current_user_id
        )
    )
    pr = pr_result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    # Count by severity
    severity_counts = {}
    for sev in Severity:
        count_result = await db.execute(
            select(func.count(Analysis.id)).where(
                Analysis.pr_id == pr_id,
                Analysis.severity == sev,
                Analysis.is_dismissed == False
            )
        )
        severity_counts[sev.value] = count_result.scalar() or 0

    # Count by type
    type_counts = {}
    for atype in AnalysisType:
        count_result = await db.execute(
            select(func.count(Analysis.id)).where(
                Analysis.pr_id == pr_id,
                Analysis.analysis_type == atype,
                Analysis.is_dismissed == False
            )
        )
        type_counts[atype.value] = count_result.scalar() or 0

    total = sum(severity_counts.values())

    return AnalysisSummary(
        total=total,
        critical=severity_counts.get("critical", 0),
        high=severity_counts.get("high", 0),
        medium=severity_counts.get("medium", 0),
        low=severity_counts.get("low", 0),
        info=severity_counts.get("info", 0),
        by_type=type_counts,
        quality_score=pr.quality_score or 0.0,
        security_score=pr.security_score or 0.0,
        performance_score=pr.performance_score or 0.0,
    )


@router.patch("/{analysis_id}/dismiss")
async def dismiss_analysis(
    analysis_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss an analysis finding."""
    result = await db.execute(
        select(Analysis)
        .join(PullRequest, Analysis.pr_id == PullRequest.id)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Analysis.id == analysis_id,
            Repository.user_id == current_user_id
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis.is_dismissed = True
    await db.commit()
    return {"message": "Analysis dismissed"}


@router.patch("/{analysis_id}/verify")
async def verify_analysis(
    analysis_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Mark an analysis finding as verified."""
    result = await db.execute(
        select(Analysis)
        .join(PullRequest, Analysis.pr_id == PullRequest.id)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Analysis.id == analysis_id,
            Repository.user_id == current_user_id
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis.is_verified = True
    await db.commit()
    return {"message": "Analysis verified"}
