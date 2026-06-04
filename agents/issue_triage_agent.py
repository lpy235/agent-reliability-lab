from __future__ import annotations

import re
import time
from typing import Any

from tracing.sdk import Trace
from tracing.store import SQLiteTraceStore


LABEL_RULES = {
    "bug": {"crash", "crashes", "error", "exception", "fail", "fails", "freeze", "freezes", "broken", "regression"},
    "feature": {"add", "support", "feature", "request", "enhancement", "allow", "new"},
    "docs": {"docs", "documentation", "readme", "typo", "example", "guide"},
    "question": {"how", "why", "question", "clarify", "help", "what"},
}

HIGH_PRIORITY_TERMS = {"crash", "crashes", "data loss", "security", "production", "unavailable", "regression"}


class IssueTriageAgent:
    def __init__(self, store: SQLiteTraceStore | None = None):
        self.store = store or SQLiteTraceStore("runs.db")

    def triage(self, title: str, body: str = "", repo: dict[str, Any] | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        repo = repo or {}
        trace = Trace.start(
            store=self.store,
            agent_name="issue_triage",
            input={"title": title, "body": body, "repo": repo},
        )
        try:
            text = f"{title}\n{body}"
            with trace.step("analyze_issue") as step:
                step.log_state(before={"title": title, "body_length": len(body)})
                label = classify_issue(text)
                priority = infer_priority(text, label)
                step.log_event({"type": "classification", "label": label, "priority": priority})
                step.log_decision({"next_action": "search_similar_issues", "reason_tags": [label, priority]})
                step.log_state(after={"label": label, "priority": priority})

            tool_calls = [
                self._record_tool_call(trace, "search_similar_issues", {"query": title}, {"matches": []}),
                self._record_tool_call(trace, "infer_owner", {"label": label, "repo": repo}, {"owner": "unassigned"}),
                self._record_tool_call(trace, "assign_label", {"label": label}, {"mode": "dry_run"}),
            ]

            latency_ms = int((time.perf_counter() - started) * 1000)
            result = {
                "title": title,
                "label": label,
                "priority": priority,
                "next_action": f"dry_run_assign_label:{label}",
                "tool_calls": tool_calls,
                "latency_ms": latency_ms,
                "run_id": trace.run_id,
            }
            trace.finish(output=result, status="success", metrics={"latency_ms": latency_ms, "tool_call_count": len(tool_calls)})
            return result
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            trace.finish(output=None, status="error", metrics={"latency_ms": latency_ms}, error=str(exc))
            raise

    def _record_tool_call(
        self,
        trace: Trace,
        name: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
    ) -> dict[str, Any]:
        call = {"name": name, "mode": "dry_run", "arguments": arguments, "result": result}
        with trace.step(name) as step:
            step.log_state(before={"tool": name})
            step.log_event({"type": "tool_call", **call})
            step.log_decision({"next_action": "continue", "reason_tags": ["dry_run_tool"]})
            step.log_state(after={"mode": "dry_run"})
        return call


def classify_issue(text: str) -> str:
    tokens = _tokens(text)
    for label in ("bug", "docs", "feature", "question"):
        if tokens & LABEL_RULES[label]:
            return label
    return "question"


def infer_priority(text: str, label: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in HIGH_PRIORITY_TERMS):
        return "high"
    if label in {"bug", "feature"}:
        return "medium"
    return "low"


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))
