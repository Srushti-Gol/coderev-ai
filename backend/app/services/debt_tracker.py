import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DebtScore:
    overall: float
    security: float
    quality: float
    performance: float
    maintainability: float
    test_coverage: float
    breakdown: Dict[str, Any]


class DebtTracker:
    """Calculates and tracks technical debt scores."""

    def calculate_debt_score(
        self,
        security_findings: List[Dict[str, Any]],
        quality_findings: List[Dict[str, Any]],
        performance_findings: List[Dict[str, Any]],
        ast_findings: List[Any],
        lines_of_code: int = 0,
    ) -> DebtScore:
        """
        Calculate technical debt score from analysis findings.
        Score ranges from 0 (no debt) to 100 (maximum debt).
        """
        # Security debt
        security_score = self._calculate_security_debt(security_findings)

        # Quality debt from AI review
        quality_score = self._calculate_quality_debt(quality_findings, ast_findings)

        # Performance debt
        performance_score = self._calculate_performance_debt(performance_findings)

        # Maintainability debt from AST findings
        maintainability_score = self._calculate_maintainability_debt(ast_findings, lines_of_code)

        # Test coverage (estimated - 0 if no test suggestions found)
        test_score = 50.0  # Default midpoint; would integrate with coverage reports

        # Weighted overall score
        overall = (
            security_score * 0.30 +
            quality_score * 0.25 +
            performance_score * 0.20 +
            maintainability_score * 0.15 +
            test_score * 0.10
        )

        breakdown = {
            "security_issues": len(security_findings),
            "quality_issues": len(quality_findings),
            "performance_issues": len(performance_findings),
            "ast_issues": len(ast_findings) if hasattr(ast_findings, '__len__') else 0,
            "severity_breakdown": self._get_severity_breakdown(
                security_findings + quality_findings + performance_findings
            ),
        }

        return DebtScore(
            overall=round(overall, 1),
            security=round(security_score, 1),
            quality=round(quality_score, 1),
            performance=round(performance_score, 1),
            maintainability=round(maintainability_score, 1),
            test_coverage=round(test_score, 1),
            breakdown=breakdown,
        )

    def _calculate_security_debt(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate security debt score (0-100)."""
        if not findings:
            return 0.0

        weights = {"critical": 25, "high": 10, "medium": 4, "low": 1, "info": 0}
        total_weight = sum(weights.get(f.get("severity", "low"), 1) for f in findings)
        return min(100.0, float(total_weight))

    def _calculate_quality_debt(
        self,
        ai_findings: List[Dict[str, Any]],
        ast_findings: List[Any]
    ) -> float:
        """Calculate code quality debt score."""
        score = 0.0
        weights = {"critical": 15, "high": 8, "medium": 3, "low": 1}

        for finding in ai_findings:
            score += weights.get(finding.get("severity", "low"), 1)

        # AST-based findings
        for finding in (ast_findings or []):
            if hasattr(finding, 'severity'):
                score += weights.get(finding.severity, 1)

        return min(100.0, score)

    def _calculate_performance_debt(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate performance debt score."""
        if not findings:
            return 0.0

        weights = {"high": 15, "medium": 8, "low": 3}
        total = sum(weights.get(f.get("severity", "low"), 3) for f in findings)
        return min(100.0, float(total))

    def _calculate_maintainability_debt(
        self,
        ast_findings: List[Any],
        lines_of_code: int
    ) -> float:
        """Calculate maintainability debt from AST analysis."""
        score = 0.0

        for finding in (ast_findings or []):
            finding_type = getattr(finding, 'finding_type', '')
            if finding_type == "long_function":
                score += 5
            elif finding_type == "deep_nesting":
                score += 4
            elif finding_type == "high_complexity":
                metric = getattr(finding, 'metric_value', 10)
                score += min(20, (metric - 10) * 2)
            elif finding_type == "duplicate":
                score += 3

        return min(100.0, score)

    def _get_severity_breakdown(self, all_findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count of findings by severity."""
        breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in all_findings:
            severity = finding.get("severity", "low")
            if severity in breakdown:
                breakdown[severity] += 1
        return breakdown

    def compare_scores(
        self,
        current_score: DebtScore,
        previous_score: Optional[DebtScore]
    ) -> Dict[str, Any]:
        """Compare current debt score with previous measurement."""
        if not previous_score:
            return {
                "trend": "new",
                "overall_change": 0,
                "security_change": 0,
                "quality_change": 0,
                "performance_change": 0,
            }

        return {
            "trend": "improving" if current_score.overall < previous_score.overall else "degrading",
            "overall_change": round(current_score.overall - previous_score.overall, 1),
            "security_change": round(current_score.security - previous_score.security, 1),
            "quality_change": round(current_score.quality - previous_score.quality, 1),
            "performance_change": round(current_score.performance - previous_score.performance, 1),
        }


debt_tracker = DebtTracker()
