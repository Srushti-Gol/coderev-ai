import logging
from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Claude API pricing (per million tokens) as of 2024
PRICING = {
    "claude-sonnet-4-6": {
        "input": 3.00,    # $3.00 per million input tokens
        "output": 15.00,  # $15.00 per million output tokens
    },
    "claude-3-haiku-20240307": {
        "input": 0.25,
        "output": 1.25,
    },
}


@dataclass
class TokenUsage:
    model: str
    input_tokens: int
    output_tokens: int
    pr_id: int
    operation: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def cost_usd(self) -> float:
        pricing = PRICING.get(self.model, PRICING["claude-sonnet-4-6"])
        input_cost = (self.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)


class CostTracker:
    def __init__(self):
        self._usage: list[TokenUsage] = []

    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        pr_id: int,
        operation: str = "analysis"
    ) -> TokenUsage:
        """Record token usage for an API call."""
        usage = TokenUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            pr_id=pr_id,
            operation=operation,
        )
        self._usage.append(usage)
        logger.info(
            f"Token usage recorded: {operation} for PR {pr_id} - "
            f"input={input_tokens}, output={output_tokens}, "
            f"cost=${usage.cost_usd:.4f}"
        )
        return usage

    def get_pr_cost(self, pr_id: int) -> Dict[str, Any]:
        """Get total cost for a PR analysis."""
        pr_usage = [u for u in self._usage if u.pr_id == pr_id]
        total_input = sum(u.input_tokens for u in pr_usage)
        total_output = sum(u.output_tokens for u in pr_usage)
        total_cost = sum(u.cost_usd for u in pr_usage)

        return {
            "pr_id": pr_id,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost_usd": round(total_cost, 4),
            "operations": [
                {
                    "operation": u.operation,
                    "model": u.model,
                    "input_tokens": u.input_tokens,
                    "output_tokens": u.output_tokens,
                    "cost_usd": u.cost_usd,
                }
                for u in pr_usage
            ],
        }

    def get_total_cost(self) -> float:
        """Get total cost across all tracked calls."""
        return round(sum(u.cost_usd for u in self._usage), 4)


cost_tracker = CostTracker()
