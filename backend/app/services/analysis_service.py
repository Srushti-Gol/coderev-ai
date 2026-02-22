import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.pull_request import PullRequest, AIStatus
from app.models.repository import Repository
from app.models.user import User
from app.models.analysis import Analysis, AnalysisType, Severity
from app.models.technical_debt import TechnicalDebt
from app.services.ai_reviewer import ai_reviewer
from app.services.ast_analyzer import ast_analyzer
from app.services.security_scanner import security_scanner
from app.services.debt_tracker import debt_tracker
from app.core.github import get_pr_diff, get_pr_files

logger = logging.getLogger(__name__)

SEVERITY_MAP = {
    "critical": Severity.critical,
    "high": Severity.high,
    "medium": Severity.medium,
    "low": Severity.low,
    "info": Severity.info,
}

TYPE_MAP = {
    "bug": AnalysisType.bug,
    "security": AnalysisType.security,
    "performance": AnalysisType.performance,
    "quality": AnalysisType.quality,
    "readability": AnalysisType.readability,
    "best_practice": AnalysisType.best_practice,
    "test": AnalysisType.test,
    "duplicate": AnalysisType.duplicate,
    "debt": AnalysisType.debt,
}


class AnalysisService:
    """Orchestrates the full PR analysis pipeline."""

    async def analyze_pull_request(self, pr_id: int, db: AsyncSession) -> bool:
        """
        Full analysis pipeline:
        1. Fetch PR diff from GitHub
        2. Run AST analysis
        3. Run security scanning
        4. Run AI review (LangGraph)
        5. Calculate debt scores
        6. Store results
        """
        try:
            # Fetch PR and related data
            pr_result = await db.execute(
                select(PullRequest).where(PullRequest.id == pr_id)
            )
            pr = pr_result.scalar_one_or_none()
            if not pr:
                logger.error(f"PR {pr_id} not found")
                return False

            repo_result = await db.execute(
                select(Repository).where(Repository.id == pr.repo_id)
            )
            repo = repo_result.scalar_one_or_none()
            if not repo:
                logger.error(f"Repository for PR {pr_id} not found")
                return False

            user_result = await db.execute(
                select(User).where(User.id == repo.user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user or not user.access_token:
                logger.error(f"User not found or no access token for PR {pr_id}")
                return False

            logger.info(f"Starting analysis for PR #{pr.pr_number} in {repo.full_name}")

            # Fetch diff from GitHub
            diff = await get_pr_diff(user.access_token, repo.full_name, pr.pr_number)
            if not diff:
                logger.warning(f"No diff found for PR {pr_id}")
                diff = ""

            # Fetch changed files
            files_data = await get_pr_files(user.access_token, repo.full_name, pr.pr_number)
            files_changed = [f.get("filename", "") for f in files_data]

            all_analyses = []

            # 1. AST Analysis
            logger.info(f"Running AST analysis for PR {pr_id}")
            ast_findings = ast_analyzer.analyze_diff(diff)
            for finding in ast_findings:
                all_analyses.append(Analysis(
                    pr_id=pr_id,
                    analysis_type=AnalysisType.quality,
                    severity=SEVERITY_MAP.get(finding.severity, Severity.medium),
                    file_path=finding.file_path,
                    line_start=finding.line_start,
                    line_end=finding.line_end,
                    message=finding.message,
                    suggestion=finding.suggestion,
                    code_snippet=finding.code_snippet,
                    rule_id=finding.finding_type,
                ))

            # 2. Security Scanning
            logger.info(f"Running security scan for PR {pr_id}")
            security_findings = security_scanner.scan_diff(diff, repo.full_name)
            for finding in security_findings:
                all_analyses.append(Analysis(
                    pr_id=pr_id,
                    analysis_type=AnalysisType.security,
                    severity=SEVERITY_MAP.get(finding.severity, Severity.medium),
                    file_path=finding.file_path,
                    line_start=finding.line_start,
                    line_end=finding.line_end,
                    message=finding.message,
                    suggestion=finding.suggestion,
                    code_snippet=finding.code_snippet,
                    rule_id=finding.rule_id,
                ))

            # 3. AI Review (LangGraph)
            logger.info(f"Running AI review for PR {pr_id}")
            try:
                ai_results = await ai_reviewer.review_pr(
                    pr_id=pr_id,
                    repo_name=repo.full_name,
                    pr_title=pr.title,
                    pr_description=pr.body or "",
                    diff=diff,
                    files_changed=files_changed,
                )

                # Process AI findings
                for category, findings in [
                    ("code_review", ai_results.get("code_review", [])),
                    ("security", ai_results.get("security", [])),
                    ("performance", ai_results.get("performance", [])),
                    ("tests", ai_results.get("tests", [])),
                ]:
                    for finding in (findings or []):
                        if not isinstance(finding, dict):
                            continue

                        finding_type_str = finding.get("type", category)
                        if category == "tests":
                            finding_type_str = "test"

                        analysis_type = TYPE_MAP.get(finding_type_str, AnalysisType.quality)

                        all_analyses.append(Analysis(
                            pr_id=pr_id,
                            analysis_type=analysis_type,
                            severity=SEVERITY_MAP.get(
                                finding.get("severity", "medium"), Severity.medium
                            ),
                            file_path=finding.get("file_path", ""),
                            line_start=finding.get("line_start"),
                            line_end=finding.get("line_end"),
                            message=finding.get("message", ""),
                            suggestion=finding.get("suggestion", ""),
                            code_snippet=finding.get("code_snippet", ""),
                            suggested_code=finding.get("suggested_code", ""),
                            rule_id=finding.get("rule_id", ""),
                        ))

                # Update PR scores from AI analysis
                pr.quality_score = ai_results.get("quality_score", 85.0)
                pr.security_score = ai_results.get("security_score", 90.0)
                pr.performance_score = ai_results.get("performance_score", 80.0)

            except Exception as e:
                logger.error(f"AI review failed for PR {pr_id}: {e}")
                # Set default scores
                pr.quality_score = 75.0
                pr.security_score = 80.0
                pr.performance_score = 75.0

            # 4. Store analysis results
            for analysis in all_analyses:
                db.add(analysis)

            # 5. Calculate and store technical debt
            ai_security = ai_results.get("security", []) if 'ai_results' in dir() else []
            ai_quality = ai_results.get("code_review", []) if 'ai_results' in dir() else []
            ai_performance = ai_results.get("performance", []) if 'ai_results' in dir() else []

            debt_score = debt_tracker.calculate_debt_score(
                security_findings=[{"severity": f.severity.value} for f in all_analyses if f.analysis_type == AnalysisType.security],
                quality_findings=[{"severity": f.severity.value} for f in all_analyses if f.analysis_type in [AnalysisType.quality, AnalysisType.bug]],
                performance_findings=[{"severity": f.severity.value} for f in all_analyses if f.analysis_type == AnalysisType.performance],
                ast_findings=ast_findings,
            )

            tech_debt = TechnicalDebt(
                repo_id=repo.id,
                pr_id=pr_id,
                overall_score=debt_score.overall,
                security_score=debt_score.security,
                quality_score=debt_score.quality,
                performance_score=debt_score.performance,
                maintainability_score=debt_score.maintainability,
                test_coverage_score=debt_score.test_coverage,
                total_issues=len(all_analyses),
                critical_issues=sum(1 for a in all_analyses if a.severity == Severity.critical),
                high_issues=sum(1 for a in all_analyses if a.severity == Severity.high),
                medium_issues=sum(1 for a in all_analyses if a.severity == Severity.medium),
                low_issues=sum(1 for a in all_analyses if a.severity == Severity.low),
                breakdown=debt_score.breakdown,
            )
            db.add(tech_debt)

            # Update PR status
            pr.ai_status = AIStatus.completed
            pr.analyzed_at = datetime.utcnow()

            await db.commit()
            logger.info(f"Analysis completed for PR {pr_id}: {len(all_analyses)} findings")
            return True

        except Exception as e:
            logger.error(f"Analysis failed for PR {pr_id}: {e}", exc_info=True)
            # Update PR to failed status
            try:
                pr_result = await db.execute(
                    select(PullRequest).where(PullRequest.id == pr_id)
                )
                pr = pr_result.scalar_one_or_none()
                if pr:
                    pr.ai_status = AIStatus.failed
                    await db.commit()
            except Exception:
                pass
            return False


analysis_service = AnalysisService()
