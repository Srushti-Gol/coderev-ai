import asyncio
import logging
from celery import Task
from sqlalchemy import select
from datetime import datetime, timedelta

from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run an async coroutine in a synchronous context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="app.workers.tasks.analyze_pr"
)
def analyze_pr(self: Task, pr_id: int) -> dict:
    """
    Celery task to analyze a pull request.
    Runs the full AI analysis pipeline.
    """
    logger.info(f"Starting analysis task for PR {pr_id}")

    async def _analyze():
        from app.services.analysis_service import analysis_service
        async with AsyncSessionLocal() as db:
            success = await analysis_service.analyze_pull_request(pr_id, db)
            return {"pr_id": pr_id, "success": success}

    try:
        result = run_async(_analyze())
        logger.info(f"Analysis task completed for PR {pr_id}: {result}")
        return result
    except Exception as exc:
        logger.error(f"Analysis task failed for PR {pr_id}: {exc}", exc_info=True)
        try:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            # Mark PR as failed
            async def _mark_failed():
                from app.models.pull_request import PullRequest, AIStatus
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(PullRequest).where(PullRequest.id == pr_id)
                    )
                    pr = result.scalar_one_or_none()
                    if pr:
                        pr.ai_status = AIStatus.failed
                        await db.commit()

            run_async(_mark_failed())
            return {"pr_id": pr_id, "success": False, "error": str(exc)}


@celery_app.task(name="app.workers.tasks.generate_tests")
def generate_tests(pr_id: int) -> dict:
    """
    Celery task to generate test suggestions for a PR.
    """
    logger.info(f"Starting test generation for PR {pr_id}")

    async def _generate():
        from app.database import AsyncSessionLocal
        from app.models.pull_request import PullRequest
        from app.models.repository import Repository
        from app.models.user import User
        from app.core.github import get_pr_diff, get_pr_files
        from app.services.ai_reviewer import ai_reviewer
        from app.models.analysis import Analysis, AnalysisType, Severity

        async with AsyncSessionLocal() as db:
            pr_result = await db.execute(select(PullRequest).where(PullRequest.id == pr_id))
            pr = pr_result.scalar_one_or_none()
            if not pr:
                return {"error": "PR not found"}

            repo_result = await db.execute(select(Repository).where(Repository.id == pr.repo_id))
            repo = repo_result.scalar_one_or_none()

            user_result = await db.execute(select(User).where(User.id == repo.user_id))
            user = user_result.scalar_one_or_none()

            diff = await get_pr_diff(user.access_token, repo.full_name, pr.pr_number)
            files = await get_pr_files(user.access_token, repo.full_name, pr.pr_number)

            # Only run test generation
            ai_results = await ai_reviewer.review_pr(
                pr_id=pr_id,
                repo_name=repo.full_name,
                pr_title=pr.title,
                pr_description=pr.body or "",
                diff=diff or "",
                files_changed=[f.get("filename", "") for f in files],
            )

            test_suggestions = ai_results.get("tests", [])
            added = 0
            for suggestion in test_suggestions:
                if not isinstance(suggestion, dict):
                    continue
                analysis = Analysis(
                    pr_id=pr_id,
                    analysis_type=AnalysisType.test,
                    severity=Severity.medium,
                    file_path=suggestion.get("file_path", ""),
                    message=suggestion.get("message", ""),
                    suggestion=suggestion.get("suggestion", ""),
                    suggested_code=suggestion.get("suggested_code", ""),
                )
                db.add(analysis)
                added += 1

            await db.commit()
            return {"pr_id": pr_id, "tests_added": added}

    try:
        result = run_async(_generate())
        logger.info(f"Test generation completed for PR {pr_id}: {result}")
        return result
    except Exception as exc:
        logger.error(f"Test generation failed for PR {pr_id}: {exc}", exc_info=True)
        return {"pr_id": pr_id, "error": str(exc)}


@celery_app.task(name="app.workers.tasks.verify_suggestion")
def verify_suggestion(analysis_id: int) -> dict:
    """
    Celery task to verify an AI suggestion with Claude.
    Checks if the suggested fix is correct and applicable.
    """
    logger.info(f"Verifying suggestion for analysis {analysis_id}")

    async def _verify():
        from app.models.analysis import Analysis
        from app.services.ai_reviewer import ai_reviewer
        from anthropic import Anthropic
        from app.config import settings

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Analysis).where(Analysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()
            if not analysis:
                return {"error": "Analysis not found"}

            client = Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Verify this code review suggestion:

Issue: {analysis.message}
Code: {analysis.code_snippet}
Suggested Fix: {analysis.suggestion}

Is this suggestion correct and actionable? Reply with just "valid" or "invalid" and a brief reason."""
                }]
            )

            verdict = response.content[0].text.strip().lower()
            is_valid = "valid" in verdict and "invalid" not in verdict

            analysis.is_verified = is_valid
            await db.commit()

            return {"analysis_id": analysis_id, "is_valid": is_valid}

    try:
        return run_async(_verify())
    except Exception as exc:
        logger.error(f"Verification failed for analysis {analysis_id}: {exc}")
        return {"analysis_id": analysis_id, "error": str(exc)}


@celery_app.task(name="app.workers.tasks.sync_open_prs")
def sync_open_prs() -> dict:
    """
    Celery beat task to sync open PRs from GitHub.
    Runs hourly to keep PR status up to date.
    """
    logger.info("Starting scheduled open PR sync")

    async def _sync():
        from app.models.pull_request import PullRequest, PRStatus
        from app.models.repository import Repository
        from app.models.user import User
        from app.core.github import get_github_client

        async with AsyncSessionLocal() as db:
            # Get all open PRs from active repos
            result = await db.execute(
                select(PullRequest, Repository, User)
                .join(Repository, PullRequest.repo_id == Repository.id)
                .join(User, Repository.user_id == User.id)
                .where(
                    PullRequest.status == PRStatus.open,
                    Repository.is_active == True
                )
                .limit(100)
            )
            rows = result.all()
            synced = 0

            for pr, repo, user in rows:
                try:
                    gh = get_github_client(user.access_token)
                    gh_repo = gh.get_repo(repo.full_name)
                    gh_pr = gh_repo.get_pull(pr.pr_number)

                    pr.title = gh_pr.title
                    if gh_pr.state == "closed":
                        pr.status = PRStatus.merged if gh_pr.merged else PRStatus.closed
                    pr.additions = gh_pr.additions
                    pr.deletions = gh_pr.deletions
                    synced += 1
                except Exception as e:
                    logger.warning(f"Failed to sync PR {pr.id}: {e}")

            await db.commit()
            return {"synced": synced}

    try:
        return run_async(_sync())
    except Exception as exc:
        logger.error(f"PR sync failed: {exc}")
        return {"error": str(exc)}


@celery_app.task(name="app.workers.tasks.cleanup_old_results")
def cleanup_old_results() -> dict:
    """
    Celery beat task to clean up old analysis results.
    Keeps database size manageable.
    """
    logger.info("Starting cleanup of old analysis results")

    async def _cleanup():
        from app.models.analysis import Analysis
        from sqlalchemy import delete

        cutoff = datetime.utcnow() - timedelta(days=90)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                delete(Analysis).where(Analysis.created_at < cutoff)
            )
            await db.commit()
            return {"deleted": result.rowcount}

    try:
        return run_async(_cleanup())
    except Exception as exc:
        logger.error(f"Cleanup failed: {exc}")
        return {"error": str(exc)}


@celery_app.task(name="app.workers.tasks.recalculate_debt_scores")
def recalculate_debt_scores() -> dict:
    """
    Celery beat task to recalculate technical debt scores.
    Runs nightly to aggregate debt across all repos.
    """
    logger.info("Starting debt score recalculation")

    async def _recalculate():
        from app.models.repository import Repository
        from app.models.analysis import Analysis, AnalysisType
        from app.models.pull_request import PullRequest
        from app.models.technical_debt import TechnicalDebt
        from app.services.debt_tracker import debt_tracker

        async with AsyncSessionLocal() as db:
            repos_result = await db.execute(
                select(Repository).where(Repository.is_active == True)
            )
            repos = repos_result.scalars().all()
            recalculated = 0

            for repo in repos:
                try:
                    # Get recent analyses
                    analyses_result = await db.execute(
                        select(Analysis)
                        .join(PullRequest, Analysis.pr_id == PullRequest.id)
                        .where(
                            PullRequest.repo_id == repo.id,
                            Analysis.is_dismissed == False
                        )
                        .limit(500)
                    )
                    analyses = analyses_result.scalars().all()

                    if not analyses:
                        continue

                    sec_findings = [{"severity": a.severity.value} for a in analyses if a.analysis_type == AnalysisType.security]
                    qual_findings = [{"severity": a.severity.value} for a in analyses if a.analysis_type in [AnalysisType.quality, AnalysisType.bug]]
                    perf_findings = [{"severity": a.severity.value} for a in analyses if a.analysis_type == AnalysisType.performance]

                    score = debt_tracker.calculate_debt_score(sec_findings, qual_findings, perf_findings, [])

                    tech_debt = TechnicalDebt(
                        repo_id=repo.id,
                        overall_score=score.overall,
                        security_score=score.security,
                        quality_score=score.quality,
                        performance_score=score.performance,
                        maintainability_score=score.maintainability,
                        test_coverage_score=score.test_coverage,
                        total_issues=len(analyses),
                        breakdown=score.breakdown,
                    )
                    db.add(tech_debt)
                    recalculated += 1
                except Exception as e:
                    logger.warning(f"Failed to recalculate debt for repo {repo.id}: {e}")

            await db.commit()
            return {"recalculated": recalculated}

    try:
        return run_async(_recalculate())
    except Exception as exc:
        logger.error(f"Debt recalculation failed: {exc}")
        return {"error": str(exc)}
