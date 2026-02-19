import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ASTFinding:
    finding_type: str  # duplicate, complexity, long_function, deep_nesting, dead_code
    severity: str
    message: str
    suggestion: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    metric_value: Optional[float] = None


class ASTAnalyzer:
    """
    AST-based code analysis using tree-sitter and regex patterns.
    Detects code quality issues like duplicate blocks, complexity, etc.
    """

    MAX_FUNCTION_LINES = 50
    MAX_NESTING_DEPTH = 4
    MAX_CYCLOMATIC_COMPLEXITY = 10
    MIN_DUPLICATE_LINES = 6

    def analyze_diff(self, diff: str) -> List[ASTFinding]:
        """Analyze a git diff for code quality issues."""
        findings = []
        current_file = ""
        added_lines = []
        line_number = 0

        file_blocks: Dict[str, List[Tuple[int, str]]] = {}

        for line in diff.split("\n"):
            if line.startswith("+++"):
                # Save previous file's added lines
                if current_file and added_lines:
                    file_blocks[current_file] = added_lines

                current_file = line[6:].strip()
                added_lines = []
                line_number = 0
            elif line.startswith("@@"):
                match = re.search(r'\+(\d+)', line)
                if match:
                    line_number = int(match.group(1)) - 1
            elif line.startswith("+") and not line.startswith("+++"):
                line_number += 1
                added_lines.append((line_number, line[1:]))
            elif not line.startswith("-"):
                line_number += 1

        if current_file and added_lines:
            file_blocks[current_file] = added_lines

        # Analyze each file
        for file_path, lines in file_blocks.items():
            if self._is_analyzable_file(file_path):
                content = "\n".join(code for _, code in lines)
                file_findings = self.analyze_code(content, file_path, lines)
                findings.extend(file_findings)

        return findings

    def _is_analyzable_file(self, file_path: str) -> bool:
        """Check if file should be analyzed."""
        skip_extensions = {'.json', '.md', '.txt', '.yml', '.yaml', '.xml', '.html', '.css'}
        for ext in skip_extensions:
            if file_path.endswith(ext):
                return False
        return True

    def analyze_code(
        self,
        content: str,
        file_path: str,
        line_mapping: Optional[List[Tuple[int, str]]] = None
    ) -> List[ASTFinding]:
        """Analyze code content for quality issues."""
        findings = []

        lines = content.split("\n")

        # Check for long functions
        findings.extend(self._detect_long_functions(lines, file_path))

        # Check for deep nesting
        findings.extend(self._detect_deep_nesting(lines, file_path))

        # Check for high cyclomatic complexity
        findings.extend(self._detect_high_complexity(lines, file_path))

        # Check for duplicate code blocks
        findings.extend(self._detect_duplicates(lines, file_path))

        # Check for dead code patterns
        findings.extend(self._detect_dead_code(lines, file_path))

        return findings

    def _detect_long_functions(self, lines: List[str], file_path: str) -> List[ASTFinding]:
        """Detect functions that are too long."""
        findings = []
        function_patterns = [
            r'^\s*def\s+(\w+)\s*\(',          # Python
            r'^\s*(async\s+)?function\s+(\w+)', # JavaScript
            r'^\s*(public|private|protected)?\s+\w+\s+(\w+)\s*\(',  # Java/C#
        ]

        in_function = False
        function_start = 0
        function_name = ""
        brace_depth = 0
        indent_level = -1

        for i, line in enumerate(lines, 1):
            for pattern in function_patterns:
                match = re.match(pattern, line)
                if match:
                    if in_function and (i - function_start) > self.MAX_FUNCTION_LINES:
                        findings.append(ASTFinding(
                            finding_type="long_function",
                            severity="medium",
                            message=f"Function '{function_name}' is too long ({i - function_start} lines). Consider breaking it into smaller functions.",
                            suggestion=f"Refactor '{function_name}' into smaller, single-responsibility functions. Aim for functions under {self.MAX_FUNCTION_LINES} lines.",
                            file_path=file_path,
                            line_start=function_start,
                            line_end=i,
                            code_snippet=lines[function_start - 1] if function_start > 0 else line,
                            metric_value=float(i - function_start),
                        ))

                    function_name = match.group(1) if match.lastindex >= 1 else "unknown"
                    function_start = i
                    in_function = True
                    indent_level = len(line) - len(line.lstrip())
                    break

        return findings

    def _detect_deep_nesting(self, lines: List[str], file_path: str) -> List[ASTFinding]:
        """Detect deeply nested code blocks."""
        findings = []
        max_depth_seen = 0
        max_depth_line = 0
        current_depth = 0

        for i, line in enumerate(lines, 1):
            # Count indentation as proxy for nesting depth
            stripped = line.lstrip()
            if not stripped:
                continue

            indent = len(line) - len(stripped)
            # Assume 4 spaces or 1 tab per level
            depth = indent // 4

            if depth > max_depth_seen:
                max_depth_seen = depth
                max_depth_line = i

            # Check for specific nesting keywords
            nesting_keywords = ['if ', 'else:', 'elif ', 'for ', 'while ', 'try:', 'except', 'with ']
            if any(stripped.startswith(kw) for kw in nesting_keywords):
                if depth >= self.MAX_NESTING_DEPTH:
                    findings.append(ASTFinding(
                        finding_type="deep_nesting",
                        severity="medium",
                        message=f"Code is nested {depth} levels deep at line {i}. Deep nesting reduces readability.",
                        suggestion="Extract nested blocks into separate functions. Use early returns to reduce nesting. Consider using guard clauses.",
                        file_path=file_path,
                        line_start=i,
                        line_end=i,
                        code_snippet=line.strip(),
                        metric_value=float(depth),
                    ))

        return findings

    def _detect_high_complexity(self, lines: List[str], file_path: str) -> List[ASTFinding]:
        """Detect high cyclomatic complexity in functions."""
        findings = []
        in_function = False
        function_start = 0
        function_name = ""
        complexity = 1

        complexity_keywords = [
            r'\bif\b', r'\belif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b',
            r'\btry\b', r'\bexcept\b', r'\band\b', r'\bor\b', r'\b\?\s',
            r'case\s+\w+:',
        ]

        function_pattern = re.compile(r'^\s*def\s+(\w+)\s*\(')

        for i, line in enumerate(lines, 1):
            fn_match = function_pattern.match(line)
            if fn_match:
                # Check previous function
                if in_function and complexity > self.MAX_CYCLOMATIC_COMPLEXITY:
                    findings.append(ASTFinding(
                        finding_type="high_complexity",
                        severity="high",
                        message=f"Function '{function_name}' has high cyclomatic complexity ({complexity}). This makes it hard to test and maintain.",
                        suggestion=f"Refactor '{function_name}' to reduce complexity. Extract conditions into named functions, use polymorphism, or simplify the logic.",
                        file_path=file_path,
                        line_start=function_start,
                        line_end=i,
                        code_snippet=lines[function_start - 1] if function_start > 0 else "",
                        metric_value=float(complexity),
                    ))

                function_name = fn_match.group(1)
                function_start = i
                complexity = 1
                in_function = True
            elif in_function:
                for pattern in complexity_keywords:
                    if re.search(pattern, line):
                        complexity += 1

        # Check last function
        if in_function and complexity > self.MAX_CYCLOMATIC_COMPLEXITY:
            findings.append(ASTFinding(
                finding_type="high_complexity",
                severity="high",
                message=f"Function '{function_name}' has high cyclomatic complexity ({complexity})",
                suggestion="Refactor to reduce complexity by extracting helper functions",
                file_path=file_path,
                line_start=function_start,
                line_end=len(lines),
                code_snippet=lines[function_start - 1] if function_start > 0 else "",
                metric_value=float(complexity),
            ))

        return findings

    def _detect_duplicates(self, lines: List[str], file_path: str) -> List[ASTFinding]:
        """Detect duplicate code blocks."""
        findings = []
        # Create normalized blocks of MIN_DUPLICATE_LINES lines
        blocks = {}
        min_lines = self.MIN_DUPLICATE_LINES

        for i in range(len(lines) - min_lines + 1):
            block = lines[i:i + min_lines]
            # Normalize: remove comments and blank lines, strip whitespace
            normalized = "\n".join(
                re.sub(r'#.*$', '', line).strip()
                for line in block
                if line.strip() and not line.strip().startswith('#')
            )

            if len(normalized) < 50:  # Skip tiny blocks
                continue

            if normalized in blocks:
                first_occurrence = blocks[normalized]
                findings.append(ASTFinding(
                    finding_type="duplicate",
                    severity="low",
                    message=f"Duplicate code block detected (first seen at line {first_occurrence}, repeated at line {i + 1})",
                    suggestion="Extract the duplicate code into a reusable function or method to follow the DRY (Don't Repeat Yourself) principle.",
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=i + min_lines,
                    code_snippet="\n".join(lines[i:i + 3]),  # Show first 3 lines
                ))
            else:
                blocks[normalized] = i + 1

        return findings

    def _detect_dead_code(self, lines: List[str], file_path: str) -> List[ASTFinding]:
        """Detect potential dead code patterns."""
        findings = []

        dead_code_patterns = [
            (r'^\s*#\s*TODO.*remove|^\s*#\s*FIXME.*remove', "low", "TODO/FIXME marked for removal"),
            (r'^\s*pass\s*$', "low", "Empty pass statement - consider removing if not needed"),
            (r'^\s*return\s*$', "info", "Empty return statement"),
            (r'(?i)#\s*(disabled?|dead\s*code|not\s*used|deprecated)', "low", "Commented-out or disabled code detected"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, severity, message in dead_code_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(ASTFinding(
                        finding_type="dead_code",
                        severity=severity,
                        message=message,
                        suggestion="Review this code. If it's no longer needed, remove it. If needed, document why it's kept.",
                        file_path=file_path,
                        line_start=i,
                        line_end=i,
                        code_snippet=line.strip(),
                    ))

        return findings

    def calculate_metrics(self, content: str, file_path: str) -> Dict[str, Any]:
        """Calculate code metrics for a file."""
        lines = content.split("\n")
        non_empty_lines = [l for l in lines if l.strip()]
        comment_lines = [l for l in lines if l.strip().startswith(('#', '//', '/*', '*'))]

        return {
            "total_lines": len(lines),
            "code_lines": len(non_empty_lines) - len(comment_lines),
            "comment_lines": len(comment_lines),
            "blank_lines": len(lines) - len(non_empty_lines),
            "file_path": file_path,
        }


ast_analyzer = ASTAnalyzer()
