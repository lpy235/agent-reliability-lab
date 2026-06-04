from __future__ import annotations

from typing import Any

from tracing.models import RunRecord, StepRecord
from tracing.store import SQLiteTraceStore


class TraceStep:
    def __init__(self, trace: "Trace", name: str):
        self.trace = trace
        self.record = StepRecord.start(run_id=trace.run_id, name=name)

    def __enter__(self) -> "TraceStep":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None:
            self.log_event({"type": "error", "message": str(exc)})
        self.record.finish(
            state_after=self.record.state_after,
            decision=self.record.decision,
            reason_tags=self.record.reason_tags,
        )
        self.trace.store.create_step(self.record)

    def log_state(self, before: dict[str, Any] | None = None, after: dict[str, Any] | None = None) -> None:
        if before is not None:
            self.record.state_before = before
        if after is not None:
            self.record.state_after = after

    def log_event(self, event: dict[str, Any]) -> None:
        self.record.events.append(event)

    def log_decision(self, decision: dict[str, Any]) -> None:
        self.record.decision = decision
        self.record.reason_tags = list(decision.get("reason_tags", []))


class Trace:
    def __init__(self, store: SQLiteTraceStore, run: RunRecord):
        self.store = store
        self.run = run
        self.run_id = run.run_id

    @classmethod
    def start(cls, store: SQLiteTraceStore, agent_name: str, input: dict[str, Any]) -> "Trace":
        store.init_schema()
        run = RunRecord.start(agent_name=agent_name, input=input)
        store.create_run(run)
        return cls(store=store, run=run)

    def step(self, name: str) -> TraceStep:
        return TraceStep(trace=self, name=name)

    def finish(
        self,
        output: dict[str, Any] | None = None,
        status: str = "success",
        metrics: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        self.store.update_run(self.run_id, status=status, output=output, metrics=metrics or {}, error=error)
