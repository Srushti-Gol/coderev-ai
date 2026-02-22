import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.security_scanner import SecurityScanner, SecurityFinding
from app.services.ast_analyzer import ASTAnalyzer, ASTFinding
from app.services.debt_tracker import DebtTracker


class TestSecurityScanner:
    """Test the security scanner service."""

    def setup_method(self):
        self.scanner = SecurityScanner()

    def test_detect_sql_injection(self):
        """Test detection of SQL injection patterns."""
        code = 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")'
        findings = self.scanner.scan_line(code, "test.py", 1)
        sql_findings = [f for f in findings if f.rule_id == "sql_injection"]
        assert len(sql_findings) > 0

    def test_detect_hardcoded_secret(self):
        """Test detection of hardcoded secrets."""
        code = 'api_key = "sk-abc123def456ghi789jkl012mno345"'
        findings = self.scanner.scan_line(code, "config.py", 10)
        secret_findings = [f for f in findings if f.rule_id == "hardcoded_secret"]
        assert len(secret_findings) > 0

    def test_detect_xss(self):
        """Test detection of XSS vulnerabilities."""
        code = 'element.innerHTML = request.query.get("name")'
        findings = self.scanner.scan_line(code, "app.js", 5)
        xss_findings = [f for f in findings if f.rule_id == "xss"]
        assert len(xss_findings) > 0

    def test_no_false_positives_for_safe_code(self):
        """Test that safe code does not trigger findings."""
        code = 'result = db.query(User).filter(User.id == user_id).first()'
        findings = self.scanner.scan_line(code, "models.py", 1)
        sql_findings = [f for f in findings if f.rule_id == "sql_injection"]
        assert len(sql_findings) == 0

    def test_scan_diff_multiple_files(self):
        """Test scanning a git diff with multiple files."""
        diff = """diff --git a/app.py b/app.py
+++ b/app.py
@@ -1,5 +1,8 @@
+import os
+password = "secret123"
+cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")
 normal_code = True
"""
        findings = self.scanner.scan_diff(diff)
        assert len(findings) > 0
        assert any(f.rule_id == "hardcoded_secret" for f in findings)

    def test_path_traversal_detection(self):
        """Test detection of path traversal vulnerabilities."""
        code = 'open(os.path.join("/uploads", request.form["filename"]))'
        findings = self.scanner.scan_line(code, "upload.py", 20)
        pt_findings = [f for f in findings if f.rule_id == "path_traversal"]
        assert len(pt_findings) > 0

    def test_weak_crypto_detection(self):
        """Test detection of weak cryptographic algorithms."""
        code = 'hashlib.md5(password.encode()).hexdigest()'
        findings = self.scanner.scan_line(code, "auth.py", 15)
        crypto_findings = [f for f in findings if f.rule_id == "weak_crypto"]
        assert len(crypto_findings) > 0

    def test_severity_is_valid(self):
        """Test that all findings have valid severity levels."""
        code = 'api_key = "super-secret-key-12345"'
        findings = self.scanner.scan_line(code, "test.py", 1)
        valid_severities = {"critical", "high", "medium", "low", "info"}
        for finding in findings:
            assert finding.severity in valid_severities


class TestASTAnalyzer:
    """Test the AST analyzer service."""

    def setup_method(self):
        self.analyzer = ASTAnalyzer()

    def test_detect_long_function(self):
        """Test detection of overly long functions."""
        # Create a function with many lines
        lines = ["def long_function():"] + ["    x = 1" for _ in range(60)]
        content = "\n".join(lines)
        findings = self.analyzer.analyze_code(content, "test.py")
        long_fn_findings = [f for f in findings if f.finding_type == "long_function"]
        assert len(long_fn_findings) > 0

    def test_detect_deep_nesting(self):
        """Test detection of deeply nested code."""
        content = """
def process():
    for item in items:
        if condition:
            for sub in item:
                if sub_condition:
                    while True:
                        if deep:
                            result = "too deep"
"""
        findings = self.analyzer.analyze_code(content, "test.py")
        nesting_findings = [f for f in findings if f.finding_type == "deep_nesting"]
        assert len(nesting_findings) > 0

    def test_detect_duplicate_code(self):
        """Test detection of duplicate code blocks."""
        block = "\n".join([f"    result_{i} = process(item_{i})" for i in range(8)])
        content = f"""
def function_a():
{block}

def function_b():
{block}
"""
        findings = self.analyzer.analyze_code(content, "test.py")
        dup_findings = [f for f in findings if f.finding_type == "duplicate"]
        assert len(dup_findings) > 0

    def test_no_findings_for_clean_code(self):
        """Test that clean code has minimal findings."""
        content = """
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b


def multiply(a: int, b: int) -> int:
    \"\"\"Multiply two numbers.\"\"\"
    return a * b
"""
        findings = self.analyzer.analyze_code(content, "math.py")
        # Clean code should have no or very few findings
        assert len(findings) < 3

    def test_calculate_metrics(self):
        """Test code metrics calculation."""
        content = """
# This is a comment
def hello():
    print("Hello")

x = 1
"""
        metrics = self.analyzer.calculate_metrics(content, "test.py")
        assert "total_lines" in metrics
        assert "code_lines" in metrics
        assert "comment_lines" in metrics
        assert metrics["total_lines"] > 0

    def test_skip_non_code_files(self):
        """Test that non-code files are skipped."""
        assert not self.analyzer._is_analyzable_file("readme.md")
        assert not self.analyzer._is_analyzable_file("config.json")
        assert self.analyzer._is_analyzable_file("app.py")
        assert self.analyzer._is_analyzable_file("main.ts")


class TestDebtTracker:
    """Test the technical debt tracker."""

    def setup_method(self):
        self.tracker = DebtTracker()

    def test_calculate_zero_debt(self):
        """Test that no findings result in zero debt."""
        score = self.tracker.calculate_debt_score([], [], [], [])
        assert score.overall == 0.0
        assert score.security == 0.0
        assert score.quality == 0.0

    def test_calculate_high_security_debt(self):
        """Test that critical security findings increase security debt."""
        security_findings = [
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "high"},
        ]
        score = self.tracker.calculate_debt_score(security_findings, [], [], [])
        assert score.security > 50
        assert score.overall > 0

    def test_overall_score_weighted(self):
        """Test that overall score is weighted average."""
        security_findings = [{"severity": "critical"} for _ in range(5)]
        score = self.tracker.calculate_debt_score(security_findings, [], [], [])
        # Security is 30% of overall
        assert score.overall <= score.security

    def test_compare_scores_improving(self):
        """Test score comparison shows improvement."""
        from app.services.debt_tracker import DebtScore
        current = DebtScore(10, 5, 10, 5, 8, 50, {})
        previous = DebtScore(20, 15, 20, 10, 15, 50, {})
        comparison = self.tracker.compare_scores(current, previous)
        assert comparison["trend"] == "improving"
        assert comparison["overall_change"] < 0

    def test_compare_scores_degrading(self):
        """Test score comparison shows degradation."""
        from app.services.debt_tracker import DebtScore
        current = DebtScore(30, 20, 30, 20, 25, 50, {})
        previous = DebtScore(20, 15, 20, 10, 15, 50, {})
        comparison = self.tracker.compare_scores(current, previous)
        assert comparison["trend"] == "degrading"
        assert comparison["overall_change"] > 0

    def test_compare_scores_no_previous(self):
        """Test comparison with no previous score."""
        from app.services.debt_tracker import DebtScore
        current = DebtScore(10, 5, 10, 5, 8, 50, {})
        comparison = self.tracker.compare_scores(current, None)
        assert comparison["trend"] == "new"
        assert comparison["overall_change"] == 0

    def test_max_score_capped_at_100(self):
        """Test that debt scores are capped at 100."""
        security_findings = [{"severity": "critical"} for _ in range(100)]
        score = self.tracker.calculate_debt_score(security_findings, [], [], [])
        assert score.security <= 100
        assert score.overall <= 100
