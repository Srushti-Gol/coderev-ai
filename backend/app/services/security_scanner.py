import re
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SecurityFinding:
    rule_id: str
    severity: str  # critical, high, medium, low
    message: str
    suggestion: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str


# Patterns for security vulnerabilities
SECURITY_PATTERNS = {
    # SQL Injection
    "sql_injection": {
        "patterns": [
            r'execute\s*\(\s*["\'].*?%s.*?["\']',
            r'cursor\.execute\s*\(\s*f["\'].*?{.*?}',
            r'query\s*=\s*["\'].*?"\s*\+\s*',
            r'SELECT.*?WHERE.*?\+\s*request\.',
            r'\.format\s*\(.*?request\.',
        ],
        "severity": "critical",
        "message": "Potential SQL injection vulnerability detected",
        "suggestion": "Use parameterized queries or ORM instead of string concatenation. Example: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
    },
    # Hardcoded secrets
    "hardcoded_secret": {
        "patterns": [
            r'(?i)(password|passwd|pwd|secret|api_key|apikey|token|auth_token)\s*=\s*["\'][^"\']{6,}["\']',
            r'(?i)(aws_secret|private_key|secret_key)\s*=\s*["\'][^"\']{10,}["\']',
            r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',
        ],
        "severity": "critical",
        "message": "Hardcoded secret or credential detected",
        "suggestion": "Move secrets to environment variables or a secret management service. Never commit credentials to source control.",
    },
    # XSS
    "xss": {
        "patterns": [
            r'innerHTML\s*=\s*.*?(request|params|query|body)',
            r'document\.write\s*\(.*?(request|params)',
            r'dangerouslySetInnerHTML.*?request\.',
            r'eval\s*\(.*?(request|params|query|input)',
        ],
        "severity": "high",
        "message": "Potential Cross-Site Scripting (XSS) vulnerability",
        "suggestion": "Sanitize all user inputs before rendering. Use DOMPurify for HTML content or encode special characters.",
    },
    # Path traversal
    "path_traversal": {
        "patterns": [
            r'open\s*\(\s*.*?(request\.|params\[|query\[)',
            r'os\.path\.join\s*\(.*?(request\.|params\[)',
            r'File\s*\(\s*.*?(request\.|params\[)',
            r'\.\./|\.\.\\',
        ],
        "severity": "high",
        "message": "Potential path traversal vulnerability",
        "suggestion": "Validate and sanitize file paths. Use os.path.realpath() and ensure the resolved path is within the allowed directory.",
    },
    # Command injection
    "command_injection": {
        "patterns": [
            r'os\.system\s*\(.*?(request\.|params\[|input)',
            r'subprocess\.(call|run|Popen)\s*\(.*?(request\.|params\[|input|shell=True)',
            r'exec\s*\(.*?(request\.|params\[|input)',
        ],
        "severity": "critical",
        "message": "Potential command injection vulnerability",
        "suggestion": "Avoid shell=True in subprocess calls. Use subprocess with a list of arguments and avoid passing user input directly.",
    },
    # Insecure random
    "insecure_random": {
        "patterns": [
            r'import random\b',
            r'random\.randint|random\.random\(\)',
            r'Math\.random\(\)',
        ],
        "severity": "medium",
        "message": "Use of cryptographically insecure random number generator",
        "suggestion": "For security-sensitive operations (tokens, passwords, keys), use secrets module in Python or crypto.randomBytes() in Node.js.",
    },
    # Weak crypto
    "weak_crypto": {
        "patterns": [
            r'(?i)(md5|sha1)\s*\(',
            r'hashlib\.(md5|sha1)',
            r'DES|RC4|RC2',
        ],
        "severity": "high",
        "message": "Use of weak cryptographic algorithm",
        "suggestion": "Use SHA-256 or stronger hashing algorithms. For passwords, use bcrypt, argon2, or scrypt.",
    },
    # Debug/logging sensitive data
    "sensitive_logging": {
        "patterns": [
            r'(?i)(print|log|logger)\s*\(.*?(password|token|secret|credential|key)',
            r'console\.(log|info|debug)\s*\(.*?(password|token|secret)',
        ],
        "severity": "medium",
        "message": "Potential logging of sensitive information",
        "suggestion": "Never log passwords, tokens, or other sensitive data. Mask or omit sensitive fields in log messages.",
    },
}


class SecurityScanner:
    """Scans code for security vulnerabilities using pattern matching."""

    def scan_diff(self, diff: str, repo_name: str = "") -> List[SecurityFinding]:
        """Scan a git diff for security vulnerabilities."""
        findings = []
        current_file = ""
        current_line = 0

        for line in diff.split("\n"):
            if line.startswith("+++"):
                current_file = line[6:].strip()
                current_line = 0
            elif line.startswith("@@"):
                # Parse line number from @@ -a,b +c,d @@ format
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line = int(match.group(1)) - 1
            elif line.startswith("+") and not line.startswith("+++"):
                current_line += 1
                code_line = line[1:]  # Remove the leading '+'
                line_findings = self.scan_line(code_line, current_file, current_line)
                findings.extend(line_findings)
            elif not line.startswith("-"):
                current_line += 1

        return findings

    def scan_line(self, line: str, file_path: str, line_number: int) -> List[SecurityFinding]:
        """Scan a single line of code for security issues."""
        findings = []

        for rule_id, rule in SECURITY_PATTERNS.items():
            for pattern in rule["patterns"]:
                if re.search(pattern, line, re.IGNORECASE):
                    finding = SecurityFinding(
                        rule_id=rule_id,
                        severity=rule["severity"],
                        message=rule["message"],
                        suggestion=rule["suggestion"],
                        file_path=file_path,
                        line_start=line_number,
                        line_end=line_number,
                        code_snippet=line.strip(),
                    )
                    findings.append(finding)
                    break  # Only report once per rule per line

        return findings

    def scan_file_content(self, content: str, file_path: str) -> List[SecurityFinding]:
        """Scan a full file for security vulnerabilities."""
        findings = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            line_findings = self.scan_line(line, file_path, line_num)
            findings.extend(line_findings)

        return findings

    def check_dependencies(self, requirements_content: str) -> List[SecurityFinding]:
        """Check for known vulnerable dependencies."""
        findings = []
        # Known vulnerable packages (simplified - in production use safety/osv)
        vulnerable_packages = {
            "django<2.2": ("high", "Django < 2.2 has known security vulnerabilities"),
            "flask<1.0": ("medium", "Flask < 1.0 has known security vulnerabilities"),
            "pyyaml<5.4": ("high", "PyYAML < 5.4 is vulnerable to arbitrary code execution"),
            "pillow<9.0": ("high", "Pillow < 9.0 has known security vulnerabilities"),
            "cryptography<3.3.2": ("critical", "cryptography < 3.3.2 has critical vulnerabilities"),
        }

        for line in requirements_content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for pkg_pattern, (severity, message) in vulnerable_packages.items():
                pkg_name = pkg_pattern.split("<")[0]
                if line.lower().startswith(pkg_name.lower()):
                    findings.append(SecurityFinding(
                        rule_id="vulnerable_dependency",
                        severity=severity,
                        message=f"Potentially vulnerable dependency: {message}",
                        suggestion=f"Update {pkg_name} to the latest secure version",
                        file_path="requirements.txt",
                        line_start=0,
                        line_end=0,
                        code_snippet=line,
                    ))

        return findings


security_scanner = SecurityScanner()
