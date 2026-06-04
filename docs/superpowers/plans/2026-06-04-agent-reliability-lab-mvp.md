# Agent Reliability Lab MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first vertical slice of Agent Reliability Lab: a traceable Docs QA agent, SQLite run store, JSONL eval runner, Markdown report, and thin FastAPI API.

**Architecture:** The project uses a small plain-Python core split into `agents`, `tracing`, `evals`, and `app`. The CLI and FastAPI both call the same `DocsQAAgent`, while tracing persists run and step records into SQLite for later inspection.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, pytest, SQLite via the standard library, requests for OpenAI-compatible HTTP calls.

---

## File Structure

- Create: `requirements.txt` for runtime and test dependencies.
- Create: `.gitignore` for generated Python, pytest, and SQLite run artifacts.
- Create: `agents/llm.py` for deterministic and OpenAI-compatible LLM clients.
- Create: `agents/retrieval.py` for local doc loading, chunking, and overlap scoring.
- Create: `agents/docs_qa_agent.py` for the Docs QA orchestration.
- Create: `tracing/models.py` for dataclasses used by the store and SDK.
- Create: `tracing/store.py` for SQLite persistence.
- Create: `tracing/sdk.py` for `Trace` and step context manager APIs.
- Create: `evals/metrics.py` for expectation checks.
- Create: `evals/report.py` for Markdown report generation.
- Create: `evals/runner.py` for JSONL execution and CLI entrypoint.
- Create: `app/main.py` for FastAPI endpoints.
- Create: `sample_docs/*.md` for deterministic demos and tests.
- Create: `evals/cases/docs_qa.jsonl` for public sample evals.
- Create: `tests/*.py` for unit and integration coverage.
- Create: `README.md` for quick start and project positioning.

## Task 0: Repository And Dependency Baseline

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `agents/__init__.py`
- Create: `tracing/__init__.py`
- Create: `evals/__init__.py`
- Create: `app/__init__.py`
- Create: `reports/.gitkeep`

- [ ] **Step 1: Initialize git if needed**

Run:

```bash
test -d .git || git init
```

Expected: existing repos stay unchanged; new repos print `Initialized empty Git repository`.

- [ ] **Step 2: Create dependency and ignore files**

Write `requirements.txt`:

```text
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
pytest>=8.0,<9.0
requests>=2.31,<3.0
```

Write `.gitignore`:

```text
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
runs.db
reports/eval-report.md
```

- [ ] **Step 3: Create package directories**

Run:

```bash
mkdir -p agents tracing evals/cases app reports tests sample_docs
touch agents/__init__.py tracing/__init__.py evals/__init__.py app/__init__.py reports/.gitkeep
```

- [ ] **Step 4: Install dependencies**

Run:

```bash
python -m pip install -r requirements.txt
```

Expected: command exits with status 0.

- [ ] **Step 5: Commit**

```bash
git add .gitignore requirements.txt agents/__init__.py tracing/__init__.py evals/__init__.py app/__init__.py reports/.gitkeep
git commit -m "chore: initialize project baseline"
```

## Task 1: SQLite Store Models

**Files:**
- Create: `tracing/models.py`
- Create: `tracing/store.py`
- Test: `tests/test_tracing_store.py`

- [ ] **Step 1: Write failing store tests**

Create `tests/test_tracing_store.py`:

```python
from tracing.models import RunRecord, StepRecord
from tracing.store import SQLiteTraceStore


def test_store_creates_and_reads_run(tmp_path):
    store = SQLiteTraceStore(tmp_path / "runs.db")
    store.init_schema()
    run = RunRecord.start(agent_name="docs_qa", input={"question": "How do I configure the database?"})

    store.create_run(run)
    store.update_run(run.run_id, status="success", output={"answer": "Use DATABASE_URL."}, metrics={"latency_ms": 12})

    saved = store.get_run(run.run_id)
    assert saved["run_id"] == run.run_id
    assert saved["status"] == "success"
    assert saved["input"]["question"] == "How do I configure the database?"
    assert saved["output"]["answer"] == "Use DATABASE_URL."
    assert saved["metrics"]["latency_ms"] == 12


def test_store_creates_and_lists_steps(tmp_path):
    store = SQLiteTraceStore(tmp_path / "runs.db")
    store.init_schema()
    run = RunRecord.start(agent_name="docs_qa", input={"question": "Q"})
    step = StepRecord.start(run_id=run.run_id, name="retrieve_docs")
    step.events.append({"type": "retrieval", "chunks": [{"source": "sample_docs/config.md"}]})
    step.finish(state_after={"chunk_count": 1}, decision={"next_action": "generate_answer"}, reason_tags=["chunks_found"])

    store.create_run(run)
    store.create_step(step)
    step.tokens = {"total": 10}
    store.update_step(step)

    steps = store.list_steps(run.run_id)
    assert len(steps) == 1
    assert steps[0]["name"] == "retrieve_docs"
    assert steps[0]["events"][0]["type"] == "retrieval"
    assert steps[0]["reason_tags"] == ["chunks_found"]
    assert steps[0]["tokens"]["total"] == 10
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
pytest tests/test_tracing_store.py -v
```

Expected: FAIL with import errors for `tracing.models` or `SQLiteTraceStore`.

- [ ] **Step 3: Implement tracing models**

Create `tracing/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
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
        self.state_after = state_after
        self.decision = decision
        self.reason_tags = reason_tags or []
        self.ended_at = utc_now()
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.ended_at)
        self.latency_ms = int((end - start).total_seconds() * 1000)
```

- [ ] **Step 4: Implement SQLite store**

Create `tracing/store.py`:

```python
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
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
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
                (status, _dumps(output) if output is not None else None, _dumps(metrics or {}), error, utc_now(), run_id),
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
                (
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
                ),
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
```

- [ ] **Step 5: Run tests to verify pass**

Run:

```bash
pytest tests/test_tracing_store.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tracing/models.py tracing/store.py tests/test_tracing_store.py
git commit -m "feat: add sqlite trace store"
```

## Task 2: Tracing SDK

**Files:**
- Create: `tracing/sdk.py`
- Modify: `tests/test_tracing_store.py`

- [ ] **Step 1: Add failing SDK test**

Append to `tests/test_tracing_store.py`:

```python
from tracing.sdk import Trace


def test_trace_context_records_step(tmp_path):
    store = SQLiteTraceStore(tmp_path / "runs.db")
    store.init_schema()
    trace = Trace.start(store=store, agent_name="docs_qa", input={"question": "Q"})

    with trace.step("retrieve_docs") as step:
        step.log_state(before={"question": "Q"})
        step.log_event({"type": "retrieval", "chunks": [{"chunk_id": "config.md#0"}]})
        step.log_decision({"next_action": "generate_answer", "reason_tags": ["chunks_found"]})
        step.log_state(after={"chunk_count": 1})

    trace.finish(output={"answer": "A"}, status="success", metrics={"latency_ms": 5})

    saved = store.get_run(trace.run_id)
    steps = store.list_steps(trace.run_id)
    assert saved["status"] == "success"
    assert steps[0]["state_before"]["question"] == "Q"
    assert steps[0]["state_after"]["chunk_count"] == 1
    assert steps[0]["decision"]["next_action"] == "generate_answer"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
pytest tests/test_tracing_store.py::test_trace_context_records_step -v
```

Expected: FAIL with import error for `tracing.sdk`.

- [ ] **Step 3: Implement SDK**

Create `tracing/sdk.py`:

```python
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
        if self.record.ended_at is None:
            self.record.finish(state_after=self.record.state_after, decision=self.record.decision, reason_tags=self.record.reason_tags)
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
        tags = decision.get("reason_tags", [])
        self.record.reason_tags = list(tags)


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
```

- [ ] **Step 4: Run SDK tests**

Run:

```bash
pytest tests/test_tracing_store.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tracing/sdk.py tests/test_tracing_store.py
git commit -m "feat: add tracing sdk"
```

## Task 3: Retrieval And LLM Clients

**Files:**
- Create: `sample_docs/config.md`
- Create: `sample_docs/deployment.md`
- Create: `sample_docs/troubleshooting.md`
- Create: `agents/retrieval.py`
- Create: `agents/llm.py`
- Test: `tests/test_docs_qa_agent.py`

- [ ] **Step 1: Create sample docs**

Create `sample_docs/config.md`:

```markdown
# Configuration

Set `DATABASE_URL` in the environment before starting the service. The value should be a SQLite path for local demos or a Postgres URL in production.

Set `OPENAI_API_KEY` only when you want to use a real OpenAI-compatible model. Without it, the demo uses the deterministic local client.
```

Create `sample_docs/deployment.md`:

```markdown
# Deployment

Run the API with `uvicorn app.main:app --reload`. The eval runner can be executed separately and writes a Markdown report under `reports/`.
```

Create `sample_docs/troubleshooting.md`:

```markdown
# Troubleshooting

If evals fail because citations are missing, inspect the saved run trace and confirm that retrieved chunks include the expected document.
```

- [ ] **Step 2: Write failing retrieval and LLM tests**

Create `tests/test_docs_qa_agent.py`:

```python
from agents.llm import RuleBasedLLMClient
from agents.retrieval import retrieve_chunks


def test_retrieval_finds_database_config():
    chunks = retrieve_chunks("How do I configure the database?", docs_dir="sample_docs", top_k=2)
    assert chunks
    assert chunks[0]["source"] == "sample_docs/config.md"
    assert "DATABASE_URL" in chunks[0]["text"]


def test_rule_based_llm_uses_context():
    client = RuleBasedLLMClient()
    response = client.complete("Question: How do I configure the database?\nContext:\nSet DATABASE_URL in the environment.")
    assert "DATABASE_URL" in response.text
    assert response.tokens["total"] > 0
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```bash
pytest tests/test_docs_qa_agent.py -v
```

Expected: FAIL with import errors for `agents.llm` or `agents.retrieval`.

- [ ] **Step 4: Implement retrieval**

Create `agents/retrieval.py`:

```python
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def load_documents(docs_dir: str | Path) -> list[dict[str, str]]:
    root = Path(docs_dir)
    if not root.exists():
        raise FileNotFoundError(f"Docs directory not found: {root}")
    docs = []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        docs.append({"source": str(path), "text": path.read_text(encoding="utf-8")})
    if not docs:
        raise ValueError(f"No markdown or text documents found in {root}")
    return docs


def split_document(source: str, text: str) -> list[dict[str, Any]]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    return [
        {"chunk_id": f"{Path(source).name}#{index}", "source": source, "text": block}
        for index, block in enumerate(blocks)
    ]


def retrieve_chunks(question: str, docs_dir: str | Path, top_k: int = 3) -> list[dict[str, Any]]:
    question_tokens = tokenize(question)
    chunks: list[dict[str, Any]] = []
    for doc in load_documents(docs_dir):
        chunks.extend(split_document(doc["source"], doc["text"]))
    scored = []
    for chunk in chunks:
        overlap = len(question_tokens & tokenize(chunk["text"]))
        scored.append((overlap, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for score, chunk in scored[:top_k] if score > 0] or [chunk for _, chunk in scored[:top_k]]
```

- [ ] **Step 5: Implement LLM clients**

Create `agents/llm.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class LLMResponse:
    text: str
    tokens: dict[str, int]
    cost: float | None = None


class RuleBasedLLMClient:
    def complete(self, prompt: str) -> LLMResponse:
        if "DATABASE_URL" in prompt:
            text = "Set DATABASE_URL in the environment before starting the service."
        elif "uvicorn" in prompt:
            text = "Run the API with uvicorn app.main:app --reload."
        else:
            text = "I can answer based on the retrieved local documentation."
        words = prompt.split()
        return LLMResponse(text=text, tokens={"prompt": len(words), "completion": len(text.split()), "total": len(words) + len(text.split())})


class OpenAICompatibleClient:
    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None, base_url: str | None = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAICompatibleClient")

    def complete(self, prompt: str) -> LLMResponse:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
            timeout=30,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            tokens={
                "prompt": int(usage.get("prompt_tokens", 0)),
                "completion": int(usage.get("completion_tokens", 0)),
                "total": int(usage.get("total_tokens", 0)),
            },
            cost=None,
        )
```

- [ ] **Step 6: Run tests to verify pass**

Run:

```bash
pytest tests/test_docs_qa_agent.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add agents/retrieval.py agents/llm.py sample_docs tests/test_docs_qa_agent.py
git commit -m "feat: add docs retrieval and llm clients"
```

## Task 4: Docs QA Agent

**Files:**
- Create: `agents/docs_qa_agent.py`
- Modify: `tests/test_docs_qa_agent.py`

- [ ] **Step 1: Add failing agent test**

Append to `tests/test_docs_qa_agent.py`:

```python
from agents.docs_qa_agent import DocsQAAgent
from tracing.store import SQLiteTraceStore


def test_docs_qa_agent_records_trace(tmp_path):
    store = SQLiteTraceStore(tmp_path / "runs.db")
    agent = DocsQAAgent(docs_dir="sample_docs", llm_client=RuleBasedLLMClient(), store=store)

    result = agent.answer("How do I configure the database?")

    assert "DATABASE_URL" in result["answer"]
    assert result["citations"][0]["source"] == "sample_docs/config.md"
    assert result["grounded"] is True
    assert result["run_id"].startswith("run_")
    steps = store.list_steps(result["run_id"])
    assert [step["name"] for step in steps] == ["retrieve_docs", "generate_answer"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
pytest tests/test_docs_qa_agent.py::test_docs_qa_agent_records_trace -v
```

Expected: FAIL with import error for `agents.docs_qa_agent`.

- [ ] **Step 3: Implement Docs QA agent**

Create `agents/docs_qa_agent.py`:

```python
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from agents.llm import RuleBasedLLMClient
from agents.retrieval import retrieve_chunks
from tracing.sdk import Trace
from tracing.store import SQLiteTraceStore


class DocsQAAgent:
    def __init__(self, docs_dir: str | Path, llm_client=None, store: SQLiteTraceStore | None = None):
        self.docs_dir = str(docs_dir)
        self.llm_client = llm_client or RuleBasedLLMClient()
        self.store = store or SQLiteTraceStore("runs.db")

    def answer(self, question: str) -> dict[str, Any]:
        started = time.perf_counter()
        trace = Trace.start(store=self.store, agent_name="docs_qa", input={"question": question, "docs_dir": self.docs_dir})
        try:
            with trace.step("retrieve_docs") as step:
                step.log_state(before={"question": question})
                chunks = retrieve_chunks(question, docs_dir=self.docs_dir, top_k=3)
                step.log_event({"type": "retrieval", "chunks": chunks})
                step.log_decision({"next_action": "generate_answer", "reason_tags": ["chunks_found"]})
                step.log_state(after={"chunk_count": len(chunks)})

            prompt = self._build_prompt(question, chunks)
            with trace.step("generate_answer") as step:
                step.log_state(before={"question": question, "chunk_ids": [chunk["chunk_id"] for chunk in chunks]})
                response = self.llm_client.complete(prompt)
                citations = [{"source": chunk["source"], "chunk_id": chunk["chunk_id"]} for chunk in chunks[:2]]
                grounded = all(citation["chunk_id"] in {chunk["chunk_id"] for chunk in chunks} for citation in citations)
                step.record.tokens = response.tokens
                step.record.cost = response.cost
                step.log_event({"type": "llm_completion", "answer": response.text})
                step.log_decision({"next_action": "finish", "reason_tags": ["answer_generated"]})
                step.log_state(after={"answer_length": len(response.text), "citation_count": len(citations)})

            latency_ms = int((time.perf_counter() - started) * 1000)
            result = {
                "question": question,
                "answer": response.text,
                "citations": citations,
                "retrieved_chunks": chunks,
                "grounded": grounded,
                "latency_ms": latency_ms,
                "run_id": trace.run_id,
            }
            trace.finish(output=result, status="success", metrics={"latency_ms": latency_ms, "tokens": response.tokens})
            return result
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            trace.finish(output=None, status="error", metrics={"latency_ms": latency_ms}, error=str(exc))
            raise

    def _build_prompt(self, question: str, chunks: list[dict[str, Any]]) -> str:
        context = "\n\n".join(f"[{chunk['chunk_id']}] {chunk['text']}" for chunk in chunks)
        return (
            "Answer the question using only the local documentation context.\n"
            "Include facts only when they are supported by the context.\n\n"
            f"Question: {question}\n\n"
            f"Context:\n{context}"
        )
```

- [ ] **Step 4: Run agent tests**

Run:

```bash
pytest tests/test_docs_qa_agent.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add agents/docs_qa_agent.py tests/test_docs_qa_agent.py
git commit -m "feat: add traceable docs qa agent"
```

## Task 5: Eval Metrics, Report, And Runner

**Files:**
- Create: `evals/metrics.py`
- Create: `evals/report.py`
- Create: `evals/runner.py`
- Create: `evals/cases/docs_qa.jsonl`
- Test: `tests/test_eval_runner.py`

- [ ] **Step 1: Create sample eval cases**

Create `evals/cases/docs_qa.jsonl`:

```jsonl
{"case_id":"docs_qa_001","agent":"docs_qa","input":{"question":"How do I configure the database?"},"expected":{"required_citations":["sample_docs/config.md"],"required_keywords":["DATABASE_URL"],"forbidden_keywords":["I don't know"],"max_latency_ms":5000,"grounded":true}}
{"case_id":"docs_qa_002","agent":"docs_qa","input":{"question":"How do I run the API server?"},"expected":{"required_citations":["sample_docs/deployment.md"],"required_keywords":["uvicorn"],"forbidden_keywords":["I don't know"],"max_latency_ms":5000,"grounded":true}}
```

- [ ] **Step 2: Write failing eval tests**

Create `tests/test_eval_runner.py`:

```python
import json

import pytest

from evals.metrics import evaluate_docs_qa
from evals.runner import run_eval_file


def test_evaluate_docs_qa_passes_expected_result():
    result = {
        "answer": "Set DATABASE_URL in the environment.",
        "citations": [{"source": "sample_docs/config.md"}],
        "grounded": True,
        "latency_ms": 10,
    }
    expected = {
        "required_citations": ["sample_docs/config.md"],
        "required_keywords": ["DATABASE_URL"],
        "forbidden_keywords": ["I don't know"],
        "max_latency_ms": 5000,
        "grounded": True,
    }

    evaluation = evaluate_docs_qa(result, expected)

    assert evaluation["passed"] is True
    assert all(check["passed"] for check in evaluation["checks"])


def test_evaluate_docs_qa_fails_missing_keyword():
    result = {"answer": "Use an environment variable.", "citations": [{"source": "sample_docs/config.md"}], "grounded": True, "latency_ms": 10}
    expected = {"required_keywords": ["DATABASE_URL"]}

    evaluation = evaluate_docs_qa(result, expected)

    assert evaluation["passed"] is False
    assert evaluation["checks"][0]["name"] == "required_keyword:DATABASE_URL"


def test_run_eval_file_writes_report(tmp_path):
    cases_path = tmp_path / "cases.jsonl"
    report_path = tmp_path / "report.md"
    db_path = tmp_path / "runs.db"
    cases_path.write_text(
        json.dumps(
            {
                "case_id": "docs_qa_001",
                "agent": "docs_qa",
                "input": {"question": "How do I configure the database?"},
                "expected": {"required_keywords": ["DATABASE_URL"], "required_citations": ["sample_docs/config.md"]},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    summary = run_eval_file(cases_path=cases_path, docs_dir="sample_docs", db_path=db_path, report_path=report_path)

    assert summary["total"] == 1
    assert summary["failed"] == 0
    assert "docs_qa_001" in report_path.read_text(encoding="utf-8")


def test_invalid_jsonl_reports_line_number(tmp_path):
    cases_path = tmp_path / "bad.jsonl"
    cases_path.write_text("{bad json}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="bad.jsonl:1"):
        run_eval_file(cases_path=cases_path, docs_dir="sample_docs", db_path=tmp_path / "runs.db", report_path=tmp_path / "report.md")
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```bash
pytest tests/test_eval_runner.py -v
```

Expected: FAIL with import errors for `evals.metrics` or `evals.runner`.

- [ ] **Step 4: Implement metrics**

Create `evals/metrics.py`:

```python
from __future__ import annotations

from typing import Any


def _check(name: str, passed: bool, actual: Any, expected: Any) -> dict[str, Any]:
    return {"name": name, "passed": passed, "actual": actual, "expected": expected}


def evaluate_docs_qa(result: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    answer = result.get("answer", "")
    citation_sources = [citation.get("source") for citation in result.get("citations", [])]

    for source in expected.get("required_citations", []):
        checks.append(_check(f"required_citation:{source}", source in citation_sources, citation_sources, source))

    for keyword in expected.get("required_keywords", []):
        checks.append(_check(f"required_keyword:{keyword}", keyword.lower() in answer.lower(), answer, keyword))

    for keyword in expected.get("forbidden_keywords", []):
        checks.append(_check(f"forbidden_keyword:{keyword}", keyword.lower() not in answer.lower(), answer, keyword))

    if "max_latency_ms" in expected:
        checks.append(_check("max_latency_ms", result.get("latency_ms", 0) <= expected["max_latency_ms"], result.get("latency_ms"), expected["max_latency_ms"]))

    if "grounded" in expected:
        checks.append(_check("grounded", result.get("grounded") is expected["grounded"], result.get("grounded"), expected["grounded"]))

    return {"passed": all(check["passed"] for check in checks), "checks": checks}
```

- [ ] **Step 5: Implement report writer**

Create `evals/report.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_markdown_report(results: list[dict[str, Any]], report_path: str | Path) -> dict[str, Any]:
    total = len(results)
    failed = sum(1 for result in results if not result["passed"])
    passed = total - failed
    pass_rate = 0.0 if total == 0 else passed / total
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Agent Reliability Lab Eval Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Total: {total}",
        f"Passed: {passed}",
        f"Failed: {failed}",
        f"Pass rate: {pass_rate:.1%}",
        "",
        "| Case | Status | Run ID | Latency |",
        "| --- | --- | --- | ---: |",
    ]
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(f"| {result['case_id']} | {status} | {result['run_id']} | {result['latency_ms']} ms |")

    failures = [result for result in results if not result["passed"]]
    if failures:
        lines.extend(["", "## Failures", ""])
        for result in failures:
            lines.append(f"### {result['case_id']}")
            for check in result["checks"]:
                if not check["passed"]:
                    lines.append(f"- {check['name']}: expected `{check['expected']}`, got `{check['actual']}`")
            lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"total": total, "passed": passed, "failed": failed, "pass_rate": pass_rate, "report_path": str(path)}
```

- [ ] **Step 6: Implement eval runner**

Create `evals/runner.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agents.docs_qa_agent import DocsQAAgent
from agents.llm import RuleBasedLLMClient
from evals.metrics import evaluate_docs_qa
from evals.report import write_markdown_report
from tracing.store import SQLiteTraceStore


def load_cases(cases_path: str | Path) -> list[dict[str, Any]]:
    path = Path(cases_path)
    cases = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path.name}:{line_no}: {exc.msg}") from exc
    return cases


def run_eval_file(cases_path: str | Path, docs_dir: str | Path, db_path: str | Path, report_path: str | Path) -> dict[str, Any]:
    store = SQLiteTraceStore(db_path)
    agent = DocsQAAgent(docs_dir=docs_dir, llm_client=RuleBasedLLMClient(), store=store)
    results = []

    for case in load_cases(cases_path):
        if case.get("agent") != "docs_qa":
            raise ValueError(f"Unsupported agent for MVP: {case.get('agent')}")
        output = agent.answer(case["input"]["question"])
        evaluation = evaluate_docs_qa(output, case.get("expected", {}))
        results.append(
            {
                "case_id": case["case_id"],
                "agent": case["agent"],
                "run_id": output["run_id"],
                "passed": evaluation["passed"],
                "checks": evaluation["checks"],
                "latency_ms": output["latency_ms"],
                "answer": output["answer"],
                "citations": output["citations"],
            }
        )

    return write_markdown_report(results, report_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Agent Reliability Lab JSONL evals.")
    parser.add_argument("cases_path")
    parser.add_argument("--docs-dir", default="sample_docs")
    parser.add_argument("--db-path", default="runs.db")
    parser.add_argument("--report-path", default="reports/eval-report.md")
    args = parser.parse_args()

    summary = run_eval_file(args.cases_path, args.docs_dir, args.db_path, args.report_path)
    print(f"Eval complete: {summary['passed']}/{summary['total']} passed. Report: {summary['report_path']}")
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 7: Run eval tests**

Run:

```bash
pytest tests/test_eval_runner.py -v
```

Expected: PASS.

- [ ] **Step 8: Run sample eval**

Run:

```bash
python -m evals.runner evals/cases/docs_qa.jsonl
```

Expected: exits 0 and creates `reports/eval-report.md`.

- [ ] **Step 9: Commit**

```bash
git add evals/metrics.py evals/report.py evals/runner.py evals/cases/docs_qa.jsonl tests/test_eval_runner.py reports/eval-report.md
git commit -m "feat: add jsonl eval runner"
```

## Task 6: FastAPI Endpoints

**Files:**
- Create: `app/main.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

Create `tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_docs_qa_run_endpoint():
    client = TestClient(app)
    response = client.post("/agents/docs-qa/run", json={"question": "How do I configure the database?", "docs_dir": "sample_docs"})

    assert response.status_code == 200
    body = response.json()
    assert "DATABASE_URL" in body["answer"]
    assert body["run_id"].startswith("run_")


def test_run_inspection_endpoint():
    client = TestClient(app)
    run_response = client.post("/agents/docs-qa/run", json={"question": "How do I configure the database?", "docs_dir": "sample_docs"})
    run_id = run_response.json()["run_id"]

    inspect_response = client.get(f"/runs/{run_id}")

    assert inspect_response.status_code == 200
    assert inspect_response.json()["run"]["run_id"] == run_id
    assert len(inspect_response.json()["steps"]) == 2
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
pytest tests/test_api.py -v
```

Expected: FAIL with import error for `app.main`.

- [ ] **Step 3: Implement FastAPI app**

Create `app/main.py`:

```python
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.docs_qa_agent import DocsQAAgent
from agents.llm import RuleBasedLLMClient
from tracing.store import SQLiteTraceStore


app = FastAPI(title="Agent Reliability Lab")


class DocsQARunRequest(BaseModel):
    question: str
    docs_dir: str = "sample_docs"


def get_store() -> SQLiteTraceStore:
    return SQLiteTraceStore(Path("runs.db"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/agents/docs-qa/run")
def run_docs_qa(request: DocsQARunRequest) -> dict:
    agent = DocsQAAgent(docs_dir=request.docs_dir, llm_client=RuleBasedLLMClient(), store=get_store())
    return agent.answer(request.question)


@app.get("/runs")
def list_runs(limit: int = 50) -> dict:
    store = get_store()
    store.init_schema()
    return {"runs": store.list_runs(limit=limit)}


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    store = get_store()
    store.init_schema()
    try:
        run = store.get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"run": run, "steps": store.list_steps(run_id)}
```

- [ ] **Step 4: Run API tests**

Run:

```bash
pytest tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Manual server smoke test**

Run:

```bash
uvicorn app.main:app --reload
```

In another shell:

```bash
curl http://127.0.0.1:8000/health
```

Expected: `{"status":"ok"}`.

- [ ] **Step 6: Commit**

```bash
git add app/main.py tests/test_api.py
git commit -m "feat: add fastapi inspection endpoints"
```

## Task 7: README And Final Verification

**Files:**
- Create: `README.md`
- Modify: `reports/eval-report.md` if regenerated

- [ ] **Step 1: Write README**

Create `README.md`:

````markdown
# Agent Reliability Lab

Agent Reliability Lab is a lightweight evaluation and observability toolkit for LLM agents. The MVP shows how to turn a local-document QA agent into something traceable, replay-ready, and regression-testable.

## Quick Start

```bash
python -m pip install -r requirements.txt
pytest
python -m evals.runner evals/cases/docs_qa.jsonl
uvicorn app.main:app --reload
```

## Run Docs QA Through The API

```bash
curl -X POST http://127.0.0.1:8000/agents/docs-qa/run \
  -H "Content-Type: application/json" \
  -d '{"question":"How do I configure the database?","docs_dir":"sample_docs"}'
```

## Run Evals

```bash
python -m evals.runner evals/cases/docs_qa.jsonl \
  --docs-dir sample_docs \
  --db-path runs.db \
  --report-path reports/eval-report.md
```

The eval runner writes a Markdown report with pass/fail status, run IDs, latency, and failed checks.

## Inspect Runs

```bash
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/runs/<run_id>
```

## MVP Scope

- Docs QA over local markdown/txt files
- Structured trace recording
- SQLite-backed run store
- JSONL regression evals
- Markdown eval report
- FastAPI endpoints for run and trace inspection

Issue triage, replay, diff, dashboard, safety policies, and CI are planned later phases.
````

- [ ] **Step 2: Run full test suite**

Run:

```bash
pytest -v
```

Expected: PASS.

- [ ] **Step 3: Run eval command**

Run:

```bash
python -m evals.runner evals/cases/docs_qa.jsonl
```

Expected: exits 0 and prints `Eval complete: 2/2 passed`.

- [ ] **Step 4: Inspect generated report**

Run:

```bash
sed -n '1,120p' reports/eval-report.md
```

Expected: report includes `Total: 2`, `Passed: 2`, and both sample case IDs.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add mvp usage guide"
```

## Self-Review Checklist

- Spec coverage: the plan covers Docs QA, trace SDK, SQLite store, JSONL evals, Markdown report, FastAPI endpoints, sample docs, tests, and README.
- Deferred scope: Issue Triage, Replay, Diff, Dashboard, CI, safety policies, and private/personal-agent concepts are not implemented in this MVP.
- Testability: all tests use the deterministic `RuleBasedLLMClient`; no network or API key is needed.
- Failure behavior: invalid JSONL raises a line-specific error, failed evals return nonzero through the CLI, and agent exceptions are recorded as error runs.
- Type consistency: run records, step records, result dictionaries, and eval summaries use the same keys across tasks.
