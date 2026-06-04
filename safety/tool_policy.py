from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEFAULT_TOOL_POLICY = {
    "search_similar_issues": {"mode": "dry_run", "approval_required": False},
    "infer_owner": {"mode": "dry_run", "approval_required": False},
    "assign_label": {"mode": "dry_run", "approval_required": True},
    "delete_issue": {"mode": "forbidden", "approval_required": True},
}


@dataclass
class ToolPolicyDecision:
    tool_name: str
    mode: str
    allowed: bool
    approval_required: bool
    violation: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "mode": self.mode,
            "allowed": self.allowed,
            "approval_required": self.approval_required,
            "violation": self.violation,
        }


class ToolPolicy:
    def __init__(self, rules: dict[str, dict[str, Any]] | None = None, max_tool_calls: int = 5):
        self.rules = rules or DEFAULT_TOOL_POLICY
        self.max_tool_calls = max_tool_calls

    def check_tool(self, tool_name: str, approved: bool = False) -> ToolPolicyDecision:
        rule = self.rules.get(tool_name, {"mode": "dry_run", "approval_required": False})
        mode = rule.get("mode", "dry_run")
        approval_required = bool(rule.get("approval_required", False))
        if mode == "forbidden":
            return ToolPolicyDecision(tool_name, mode, False, approval_required, "forbidden_tool")
        if approval_required and not approved:
            return ToolPolicyDecision(tool_name, mode, True, True, "approval_required")
        return ToolPolicyDecision(tool_name, mode, True, approval_required, None)

    def check_max_tool_calls(self, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(tool_calls) <= self.max_tool_calls:
            return []
        return [
            {
                "type": "max_tool_calls",
                "message": f"Tool call count {len(tool_calls)} exceeds limit {self.max_tool_calls}",
                "limit": self.max_tool_calls,
                "actual": len(tool_calls),
            }
        ]

