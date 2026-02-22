import logging
import json
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from anthropic import Anthropic
from app.config import settings
from app.services.cost_tracker import cost_tracker

logger = logging.getLogger(__name__)

# Try to import LangGraph - fall back gracefully if not available
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available, using sequential analysis")


class ReviewState(TypedDict):
    """State passed through the review graph."""
    pr_id: int
    repo_name: str
    pr_title: str
    pr_description: str
    diff: str
    files_changed: List[str]
    code_review_findings: List[Dict[str, Any]]
    security_findings: List[Dict[str, Any]]
    optimization_findings: List[Dict[str, Any]]
    test_suggestions: List[Dict[str, Any]]
    overall_summary: str
    quality_score: float
    security_score: float
    performance_score: float
    errors: List[str]


class AIReviewer:
    """
    LangGraph-based AI code reviewer using Claude claude-sonnet-4-6.
    Implements a multi-node review graph for comprehensive analysis.
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-6"
        self.graph = self._build_graph() if LANGGRAPH_AVAILABLE else None

    def _build_graph(self):
        """Build the LangGraph review workflow."""
        workflow = StateGraph(ReviewState)

        # Add nodes
        workflow.add_node("code_review", self._code_review_node)
        workflow.add_node("security_check", self._security_check_node)
        workflow.add_node("optimization", self._optimization_node)
        workflow.add_node("test_generation", self._test_generation_node)
        workflow.add_node("summarize", self._summarize_node)

        # Define edges
        workflow.set_entry_point("code_review")
        workflow.add_edge("code_review", "security_check")
        workflow.add_edge("security_check", "optimization")
        workflow.add_edge("optimization", "test_generation")
        workflow.add_edge("test_generation", "summarize")
        workflow.add_edge("summarize", END)

        return workflow.compile()

    def _call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        pr_id: int,
        operation: str,
        max_tokens: int = 4096
    ) -> str:
        """Call Claude API and track token usage."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Track token usage
            if hasattr(response, 'usage'):
                cost_tracker.record(
                    model=self.model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    pr_id=pr_id,
                    operation=operation,
                )

            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API call failed for {operation}: {e}")
            raise

    def _parse_json_response(self, text: str) -> Any:
        """Parse JSON from Claude's response."""
        # Find JSON block in response
        json_match = None
        try:
            # Try direct parse first
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Look for JSON in markdown code blocks
        import re
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}',
            r'\[[\s\S]*\]',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                try:
                    return json.loads(match.group(1) if '```' in pattern else match.group(0))
                except json.JSONDecodeError:
                    continue

        return []

    def _code_review_node(self, state: ReviewState) -> ReviewState:
        """Node: General code review for bugs, readability, best practices."""
        logger.info(f"Running code review node for PR {state['pr_id']}")

        system_prompt = """You are an expert code reviewer. Analyze the provided git diff and identify:
1. Bugs and logical errors
2. Code readability issues
3. Best practice violations
4. Missing error handling
5. API misuse

Return your findings as a JSON array where each finding has:
- type: "bug", "readability", or "best_practice"
- severity: "critical", "high", "medium", "low", or "info"
- file_path: the file being analyzed
- line_start: starting line number (integer)
- line_end: ending line number (integer)
- message: clear description of the issue
- suggestion: specific, actionable fix
- code_snippet: the problematic code (up to 5 lines)
- suggested_code: improved version if applicable

Return ONLY the JSON array, no other text."""

        diff_preview = state["diff"][:8000] if len(state["diff"]) > 8000 else state["diff"]

        user_prompt = f"""Review this pull request:

Title: {state["pr_title"]}
Description: {state.get("pr_description", "No description")}
Repository: {state["repo_name"]}

Git Diff:
```diff
{diff_preview}
```

Identify all code review issues. Focus on actual bugs and significant quality issues, not stylistic nitpicks."""

        try:
            response = self._call_claude(
                system_prompt, user_prompt,
                state["pr_id"], "code_review",
                max_tokens=4096
            )
            findings = self._parse_json_response(response)
            if not isinstance(findings, list):
                findings = []
            state["code_review_findings"] = findings
        except Exception as e:
            logger.error(f"Code review node failed: {e}")
            state["errors"] = state.get("errors", []) + [str(e)]
            state["code_review_findings"] = []

        return state

    def _security_check_node(self, state: ReviewState) -> ReviewState:
        """Node: Security vulnerability analysis."""
        logger.info(f"Running security check node for PR {state['pr_id']}")

        system_prompt = """You are a security expert specializing in code security review. Analyze the git diff for:
1. Authentication and authorization flaws
2. Input validation vulnerabilities (SQL injection, XSS, etc.)
3. Cryptography misuse
4. Sensitive data exposure
5. Insecure dependencies
6. OWASP Top 10 violations

Return findings as a JSON array where each finding has:
- type: "security"
- severity: "critical", "high", "medium", "low"
- file_path: file being analyzed
- line_start: line number
- line_end: line number
- message: security issue description
- suggestion: remediation steps
- code_snippet: vulnerable code
- rule_id: OWASP category or CVE if applicable

Return ONLY the JSON array."""

        diff_preview = state["diff"][:6000] if len(state["diff"]) > 6000 else state["diff"]

        user_prompt = f"""Security audit this pull request:

Repository: {state["repo_name"]}
Files changed: {', '.join(state.get("files_changed", [])[:10])}

Git Diff:
```diff
{diff_preview}
```

Identify ALL security vulnerabilities. Be thorough but avoid false positives."""

        try:
            response = self._call_claude(
                system_prompt, user_prompt,
                state["pr_id"], "security_check",
                max_tokens=3000
            )
            findings = self._parse_json_response(response)
            if not isinstance(findings, list):
                findings = []
            state["security_findings"] = findings
        except Exception as e:
            logger.error(f"Security check node failed: {e}")
            state["errors"] = state.get("errors", []) + [str(e)]
            state["security_findings"] = []

        return state

    def _optimization_node(self, state: ReviewState) -> ReviewState:
        """Node: Performance optimization analysis."""
        logger.info(f"Running optimization node for PR {state['pr_id']}")

        system_prompt = """You are a performance optimization expert. Analyze the code diff for:
1. Inefficient algorithms (O(n²) where O(n) is possible)
2. Database N+1 query problems
3. Unnecessary memory allocations
4. Missing caching opportunities
5. Blocking I/O in async code
6. Resource leaks

Return findings as a JSON array where each finding has:
- type: "performance"
- severity: "high", "medium", "low"
- file_path: file
- line_start: line number
- line_end: line number
- message: performance issue description
- suggestion: optimization approach
- code_snippet: inefficient code
- suggested_code: optimized version

Return ONLY the JSON array."""

        diff_preview = state["diff"][:6000] if len(state["diff"]) > 6000 else state["diff"]

        user_prompt = f"""Analyze performance in this pull request:

Repository: {state["repo_name"]}

Git Diff:
```diff
{diff_preview}
```

Focus on significant performance issues that would impact production systems."""

        try:
            response = self._call_claude(
                system_prompt, user_prompt,
                state["pr_id"], "optimization",
                max_tokens=3000
            )
            findings = self._parse_json_response(response)
            if not isinstance(findings, list):
                findings = []
            state["optimization_findings"] = findings
        except Exception as e:
            logger.error(f"Optimization node failed: {e}")
            state["errors"] = state.get("errors", []) + [str(e)]
            state["optimization_findings"] = []

        return state

    def _test_generation_node(self, state: ReviewState) -> ReviewState:
        """Node: Generate test suggestions for changed code."""
        logger.info(f"Running test generation node for PR {state['pr_id']}")

        system_prompt = """You are a testing expert. Based on the code changes, suggest tests that should be written.
For each untested function or significant code path, provide:
1. What to test (the scenario)
2. Example test code

Return findings as a JSON array where each finding has:
- type: "test"
- severity: "medium"
- file_path: file being analyzed
- line_start: relevant line
- line_end: relevant line
- message: what test is missing
- suggestion: description of what to test
- suggested_code: example test code

Return ONLY the JSON array."""

        # Only use a portion of the diff for test generation to save tokens
        diff_preview = state["diff"][:4000] if len(state["diff"]) > 4000 else state["diff"]

        user_prompt = f"""Suggest tests for this PR:

Title: {state["pr_title"]}

Git Diff:
```diff
{diff_preview}
```

Identify the most critical missing tests for the changed functionality."""

        try:
            response = self._call_claude(
                system_prompt, user_prompt,
                state["pr_id"], "test_generation",
                max_tokens=2000
            )
            findings = self._parse_json_response(response)
            if not isinstance(findings, list):
                findings = []
            state["test_suggestions"] = findings
        except Exception as e:
            logger.error(f"Test generation node failed: {e}")
            state["errors"] = state.get("errors", []) + [str(e)]
            state["test_suggestions"] = []

        return state

    def _summarize_node(self, state: ReviewState) -> ReviewState:
        """Node: Generate overall summary and scores."""
        logger.info(f"Running summarize node for PR {state['pr_id']}")

        all_findings = (
            state.get("code_review_findings", []) +
            state.get("security_findings", []) +
            state.get("optimization_findings", [])
        )

        # Calculate scores based on findings
        security_findings = state.get("security_findings", [])
        security_critical = sum(1 for f in security_findings if f.get("severity") == "critical")
        security_high = sum(1 for f in security_findings if f.get("severity") == "high")
        security_score = max(0, 100 - (security_critical * 25) - (security_high * 10))

        total_findings = len(all_findings)
        critical_findings = sum(1 for f in all_findings if f.get("severity") == "critical")
        high_findings = sum(1 for f in all_findings if f.get("severity") == "high")
        quality_score = max(0, 100 - (critical_findings * 15) - (high_findings * 8) - (total_findings * 1))
        quality_score = min(100, quality_score)

        perf_findings = state.get("optimization_findings", [])
        perf_high = sum(1 for f in perf_findings if f.get("severity") == "high")
        performance_score = max(0, 100 - (perf_high * 15) - (len(perf_findings) * 5))

        state["quality_score"] = round(float(quality_score), 1)
        state["security_score"] = round(float(security_score), 1)
        state["performance_score"] = round(float(performance_score), 1)

        # Generate summary
        summary_parts = [f"**PR Analysis Summary for: {state['pr_title']}**\n"]
        summary_parts.append(f"- Quality Score: {state['quality_score']}/100")
        summary_parts.append(f"- Security Score: {state['security_score']}/100")
        summary_parts.append(f"- Performance Score: {state['performance_score']}/100")
        summary_parts.append(f"- Total Issues Found: {total_findings}")

        if critical_findings:
            summary_parts.append(f"\n⚠️ **{critical_findings} critical issue(s) require immediate attention.**")

        state["overall_summary"] = "\n".join(summary_parts)
        return state

    async def review_pr(
        self,
        pr_id: int,
        repo_name: str,
        pr_title: str,
        pr_description: str,
        diff: str,
        files_changed: List[str],
    ) -> Dict[str, Any]:
        """
        Run the full PR review workflow.
        Returns all findings organized by category.
        """
        initial_state: ReviewState = {
            "pr_id": pr_id,
            "repo_name": repo_name,
            "pr_title": pr_title,
            "pr_description": pr_description,
            "diff": diff,
            "files_changed": files_changed,
            "code_review_findings": [],
            "security_findings": [],
            "optimization_findings": [],
            "test_suggestions": [],
            "overall_summary": "",
            "quality_score": 85.0,
            "security_score": 90.0,
            "performance_score": 80.0,
            "errors": [],
        }

        if self.graph and LANGGRAPH_AVAILABLE:
            # Use LangGraph for structured workflow
            final_state = await self.graph.ainvoke(initial_state)
        else:
            # Sequential fallback
            state = initial_state
            state = self._code_review_node(state)
            state = self._security_check_node(state)
            state = self._optimization_node(state)
            state = self._test_generation_node(state)
            state = self._summarize_node(state)
            final_state = state

        return {
            "code_review": final_state.get("code_review_findings", []),
            "security": final_state.get("security_findings", []),
            "performance": final_state.get("optimization_findings", []),
            "tests": final_state.get("test_suggestions", []),
            "summary": final_state.get("overall_summary", ""),
            "quality_score": final_state.get("quality_score", 0.0),
            "security_score": final_state.get("security_score", 0.0),
            "performance_score": final_state.get("performance_score", 0.0),
            "errors": final_state.get("errors", []),
        }


ai_reviewer = AIReviewer()
