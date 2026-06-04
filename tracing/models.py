from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RunRecord:
    run_id: str
    agent_name: str
    status: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    metrics: dict[str, Any]
    error: str | None
    started_at: str
    ended_at: str | None

    @classmethod
    def start(cls, agent_name: str, input: dict[str, Any]) -> "RunRecord":
        return cls(
            run_id=f"run_{uuid4().hex}",
            agent_name=agent_name,
            status="running",
            input=input,
            output=None,
            metrics={},
            error=None,
            started_at=utc_now(),
            ended_at=None,
        )


@dataclass
class StepRecord:
    step_id: str
    run_id: str
    name: str
    state_before: dict[str, Any] | None
    events: list[dict[str, Any]]
    decision: dict[str, Any] | None
    reason_tags: list[str]
    state_after: dict[str, Any] | None
    tokens: dict[str, Any]
    cost: float | None
    started_at: str
    ended_at: str | None
    latency_ms: int | None

    @classmethod
    def start(cls, run_id: str, name: str) -> "StepRecord":
        return cls(
            step_id=f"step_{uuid4().hex}",
            run_id=run_id,
            name=name,
            state_before=None,
            events=[],
            decision=None,
            reason_tags=[],
            state_after=None,
            tokens={},
            cost=None,
            started_at=utc_now(),
            ended_at=None,
            latency_ms=None,
        )

    def finish(
        self,
        state_after: dict[str, Any] | None = None,
        decision: dict[str, Any] | None = None,
        reason_tags: list[str] | None = None,
    ) -> None:
        if state_after is not None:
            self.state_after = state_after
        if decision is not None:
            self.decision = decision
        if reason_tags is not None:
            self.reason_tags = reason_tags
        self.ended_at = utc_now()
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.ended_at)
        self.latency_ms = int((end - start).total_seconds() * 1000)
