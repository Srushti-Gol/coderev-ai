from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.pull_request import PullRequest, PRStatus, AIStatus
from app.models.repository import Repository
from app.models.analysis import Analysis, Severity, AnalysisType
from app.models.technical_debt import TechnicalDebt
from app.core.security import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_dashboard_stats(
    days: int = Query(30, ge=7, le=365),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate dashboard statistics."""
    since = datetime.utcnow() - timedelta(days=days)

    # Total repos
    repos_result = await db.execute(
        select(func.count(Repository.id)).where(Repository.user_id == current_user_id)
    )
    total_repos = repos_result.scalar() or 0

    # Active repos
    active_repos_result = await db.execute(
        select(func.count(Repository.id)).where(
            Repository.user_id == current_user_id,
            Repository.is_active == True
        )
    )
    active_repos = active_repos_result.scalar() or 0

    # Total PRs
    total_prs_result = await db.execute(
        select(func.count(PullRequest.id))
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(Repository.user_id == current_user_id)
    )
    total_prs = total_prs_result.scalar() or 0

    # Open PRs
    open_prs_result = await db.execute(
        select(func.count(PullRequest.id))
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Repository.user_id == current_user_id,
            PullRequest.status == PRStatus.open
        )
    )
    open_prs = open_prs_result.scalar() or 0

    # PRs analyzed in period
    analyzed_result = await db.execute(
        select(func.count(PullRequest.id))
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Repository.user_id == current_user_id,
            PullRequest.ai_status == AIStatus.completed,
            PullRequest.analyzed_at >= since
        )
    )
    analyzed_prs = analyzed_result.scalar() or 0

    # Total issues found
    issues_result = await db.execute(
        select(func.count(Analysis.id))
        .join(PullRequest, Analysis.pr_id == PullRequest.id)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Repository.user_id == current_user_id,
            Analysis.created_at >= since
        )
    )
    total_issues = issues_result.scalar() or 0

    # Critical issues
    critical_result = await db.execute(
        select(func.count(Analysis.id))
        .join(PullRequest, Analysis.pr_id == PullRequest.id)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Repository.user_id == current_user_id,
            Analysis.severity == Severity.critical,
            Analysis.is_dismissed == False,
            Analysis.created_at >= since
        )
    )
    critical_issues = critical_result.scalar() or 0

    # Average quality score
    quality_result = await db.execute(
        select(func.avg(PullRequest.quality_score))
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Repository.user_id == current_user_id,
            PullRequest.quality_score.isnot(None),
            PullRequest.analyzed_at >= since
        )
    )
    avg_quality = round(quality_result.scalar() or 0.0, 1)

    return {
        "total_repos": total_repos,
        "active_repos": active_repos,
        "total_prs": total_prs,
        "open_prs": open_prs,
        "analyzed_prs": analyzed_prs,
        "total_issues": total_issues,
        "critical_issues": critical_issues,
        "avg_quality_score": avg_quality,
        "period_days": days,
    }


@router.get("/pr-velocity")
async def get_pr_velocity(
    days: int = Query(30, ge=7, le=90),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get PR velocity data (PRs opened vs merged per week)."""
    since = datetime.utcnow() - timedelta(days=days)

    prs_result = await db.execute(
        select(PullRequest)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Repository.user_id == current_user_id,
            PullRequest.created_at >= since
        )
        .order_by(PullRequest.created_at)
    )
    prs = prs_result.scalars().all()

    # Group by week
    weekly_data = {}
    for pr in prs:
        week_start = pr.created_at.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=pr.created_at.weekday())
        week_key = week_start.strftime("%Y-%m-%d")

        if week_key not in weekly_data:
            weekly_data[week_key] = {"week": week_key, "opened": 0, "merged": 0, "closed": 0}
        weekly_data[week_key]["opened"] += 1
        if pr.status == PRStatus.merged:
            weekly_data[week_key]["merged"] += 1
        elif pr.status == PRStatus.closed:
            weekly_data[week_key]["closed"] += 1

    return sorted(weekly_data.values(), key=lambda x: x["week"])


@router.get("/cycle-time")
async def get_cycle_time(
    days: int = Query(30, ge=7, le=90),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get average PR cycle time by repository."""
    since = datetime.utcnow() - timedelta(days=days)

    prs_result = await db.execute(
        select(PullRequest, Repository.name.label("repo_name"))
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Repository.user_id == current_user_id,
            PullRequest.pr_merged_at.isnot(None),
            PullRequest.pr_created_at.isnot(None),
            PullRequest.created_at >= since
        )
    )
    rows = prs_result.all()

    repo_cycle_times = {}
    for pr, repo_name in rows:
        if pr.pr_merged_at and pr.pr_created_at:
            cycle_hours = (pr.pr_merged_at - pr.pr_created_at).total_seconds() / 3600
            if repo_name not in repo_cycle_times:
                repo_cycle_times[repo_name] = []
            repo_cycle_times[repo_name].append(cycle_hours)

    result = []
    for repo_name, times in repo_cycle_times.items():
        result.append({
            "repo": repo_name,
            "avg_hours": round(sum(times) / len(times), 1),
            "min_hours": round(min(times), 1),
            "max_hours": round(max(times), 1),
            "count": len(times),
        })

    return sorted(result, key=lambda x: x["avg_hours"])


@router.get("/debt-score")
async def get_debt_score(
    repo_id: Optional[int] = None,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get technical debt score over time."""
    query = (
        select(TechnicalDebt, Repository.name.label("repo_name"))
        .join(Repository, TechnicalDebt.repo_id == Repository.id)
        .where(Repository.user_id == current_user_id)
    )
    if repo_id:
        query = query.where(TechnicalDebt.repo_id == repo_id)

    query = query.order_by(TechnicalDebt.created_at.desc()).limit(100)
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "date": debt.created_at.strftime("%Y-%m-%d"),
            "repo": repo_name,
            "overall": debt.overall_score,
            "security": debt.security_score,
            "quality": debt.quality_score,
            "performance": debt.performance_score,
            "maintainability": debt.maintainability_score,
        }
        for debt, repo_name in rows
    ]


@router.get("/quality-over-time")
async def get_quality_over_time(
    days: int = Query(30, ge=7, le=90),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get quality score trend over time."""
    since = datetime.utcnow() - timedelta(days=days)

    prs_result = await db.execute(
        select(PullRequest)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Repository.user_id == current_user_id,
            PullRequest.quality_score.isnot(None),
            PullRequest.analyzed_at >= since
        )
        .order_by(PullRequest.analyzed_at)
    )
    prs = prs_result.scalars().all()

    # Group by day
    daily_data = {}
    for pr in prs:
        day_key = pr.analyzed_at.strftime("%Y-%m-%d")
        if day_key not in daily_data:
            daily_data[day_key] = {"date": day_key, "scores": [], "count": 0}
        daily_data[day_key]["scores"].append(pr.quality_score)
        daily_data[day_key]["count"] += 1

    result = []
    for day_key, data in sorted(daily_data.items()):
        result.append({
            "date": day_key,
            "avg_quality": round(sum(data["scores"]) / len(data["scores"]), 1),
            "count": data["count"],
        })

    return result


@router.get("/weekly-digest")
async def get_weekly_digest(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get weekly digest summary."""
    since = datetime.utcnow() - timedelta(days=7)
    prev_week = since - timedelta(days=7)

    # This week stats
    this_week_prs = await db.execute(
        select(func.count(PullRequest.id))
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(Repository.user_id == current_user_id, PullRequest.created_at >= since)
    )

    this_week_issues = await db.execute(
        select(func.count(Analysis.id))
        .join(PullRequest, Analysis.pr_id == PullRequest.id)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(Repository.user_id == current_user_id, Analysis.created_at >= since)
    )

    # Previous week
    prev_week_prs = await db.execute(
        select(func.count(PullRequest.id))
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Repository.user_id == current_user_id,
            PullRequest.created_at >= prev_week,
            PullRequest.created_at < since
        )
    )

    tw_prs = this_week_prs.scalar() or 0
    pw_prs = prev_week_prs.scalar() or 0
    tw_issues = this_week_issues.scalar() or 0

    prs_change = ((tw_prs - pw_prs) / pw_prs * 100) if pw_prs > 0 else 0

    return {
        "this_week_prs": tw_prs,
        "prev_week_prs": pw_prs,
        "prs_change_pct": round(prs_change, 1),
        "this_week_issues": tw_issues,
        "period": {
            "start": since.strftime("%Y-%m-%d"),
            "end": datetime.utcnow().strftime("%Y-%m-%d"),
        },
    }


@router.get("/pr-size-distribution")
async def get_pr_size_distribution(
    days: int = Query(30, ge=7, le=90),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get PR size distribution (XS/S/M/L/XL)."""
    since = datetime.utcnow() - timedelta(days=days)

    prs_result = await db.execute(
        select(PullRequest.additions + PullRequest.deletions)
        .join(Repository, PullRequest.repo_id == Repository.id)
        .where(
            Repository.user_id == current_user_id,
            PullRequest.created_at >= since
        )
    )
    sizes = [row[0] for row in prs_result.all()]

    distribution = {"XS": 0, "S": 0, "M": 0, "L": 0, "XL": 0}
    for size in sizes:
        if size < 10:
            distribution["XS"] += 1
        elif size < 50:
            distribution["S"] += 1
        elif size < 200:
            distribution["M"] += 1
        elif size < 500:
            distribution["L"] += 1
        else:
            distribution["XL"] += 1

    return [{"name": k, "value": v} for k, v in distribution.items()]
