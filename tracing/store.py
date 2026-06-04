from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from tracing.models import RunRecord, StepRecord, utc_now


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _loads(value: str | None, default: Any) -> Any:
    if value is None:
        return default
    return json.loads(value)


class SQLiteTraceStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        parent = self.db_path.parent
        if str(parent) not in {"", "."}:
            parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    output_json TEXT,
                    metrics_json TEXT,
                    error TEXT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS steps (
                    step_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    state_before_json TEXT,
                    events_json TEXT,
                    decision_json TEXT,
                    reason_tags_json TEXT,
                    state_after_json TEXT,
                    tokens_json TEXT,
                    cost REAL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    latency_ms INTEGER,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                )
                """
            )

    def create_run(self, run: RunRecord) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, agent_name, status, input_json, output_json,
                    metrics_json, error, started_at, ended_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.agent_name,
                    run.status,
                    _dumps(run.input),
                    _dumps(run.output) if run.output is not None else None,
                    _dumps(run.metrics),
                    run.error,
                    run.started_at,
                    run.ended_at,
                ),
            )

    def update_run(
        self,
        run_id: str,
        status: str,
        output: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE runs
                SET status = ?, output_json = ?, metrics_json = ?, error = ?, ended_at = ?
                WHERE run_id = ?
                """,
                (
                    status,
                    _dumps(output) if output is not None else None,
                    _dumps(metrics or {}),
                    error,
                    utc_now(),
                    run_id,
                ),
            )

    def create_step(self, step: StepRecord) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO steps (
                    step_id, run_id, name, state_before_json, events_json,
                    decision_json, reason_tags_json, state_after_json,
                    tokens_json, cost, started_at, ended_at, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._step_values(step),
            )

    def update_step(self, step: StepRecord) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE steps
                SET state_before_json = ?, events_json = ?, decision_json = ?,
                    reason_tags_json = ?, state_after_json = ?, tokens_json = ?,
                    cost = ?, ended_at = ?, latency_ms = ?
                WHERE step_id = ?
                """,
                (
                    _dumps(step.state_before) if step.state_before is not None else None,
                    _dumps(step.events),
                    _dumps(step.decision) if step.decision is not None else None,
                    _dumps(step.reason_tags),
                    _dumps(step.state_after) if step.state_after is not None else None,
                    _dumps(step.tokens),
                    step.cost,
                    step.ended_at,
                    step.latency_ms,
                    step.step_id,
                ),
            )

    def get_run(self, run_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"Run not found: {run_id}")
        return self._row_to_run(row)

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row_to_run(row) for row in rows]

    def list_steps(self, run_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM steps WHERE run_id = ? ORDER BY started_at ASC", (run_id,)).fetchall()
        return [self._row_to_step(row) for row in rows]

    def _step_values(self, step: StepRecord) -> tuple[Any, ...]:
        return (
            step.step_id,
            step.run_id,
            step.name,
            _dumps(step.state_before) if step.state_before is not None else None,
            _dumps(step.events),
            _dumps(step.decision) if step.decision is not None else None,
            _dumps(step.reason_tags),
            _dumps(step.state_after) if step.state_after is not None else None,
            _dumps(step.tokens),
            step.cost,
            step.started_at,
            step.ended_at,
            step.latency_ms,
        )

    def _row_to_run(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "run_id": row["run_id"],
            "agent_name": row["agent_name"],
            "status": row["status"],
            "input": _loads(row["input_json"], {}),
            "output": _loads(row["output_json"], None),
            "metrics": _loads(row["metrics_json"], {}),
            "error": row["error"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
        }

    def _row_to_step(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "step_id": row["step_id"],
            "run_id": row["run_id"],
            "name": row["name"],
            "state_before": _loads(row["state_before_json"], None),
            "events": _loads(row["events_json"], []),
            "decision": _loads(row["decision_json"], None),
            "reason_tags": _loads(row["reason_tags_json"], []),
            "state_after": _loads(row["state_after_json"], None),
            "tokens": _loads(row["tokens_json"], {}),
            "cost": row["cost"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "latency_ms": row["latency_ms"],
        }
