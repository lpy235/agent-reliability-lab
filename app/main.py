from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.docs_qa_agent import DocsQAAgent
from agents.issue_triage_agent import IssueTriageAgent
from agents.llm import RuleBasedLLMClient
from tracing.diff import diff_runs
from tracing.replay import replay_run
from tracing.store import SQLiteTraceStore


app = FastAPI(title="Agent Reliability Lab")
WEB_DIR = Path(__file__).parent / "web"
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

EVAL_REPORTS = [
    ("docs_qa", "Docs QA", "eval-report.json"),
    ("issue_triage", "Issue Triage", "issue-triage-report.json"),
]


class DocsQARunRequest(BaseModel):
    question: str
    docs_dir: str = "sample_docs"


class IssueTriageRunRequest(BaseModel):
    title: str
    body: str = ""
    repo: dict = {}


class ReplayRunRequest(BaseModel):
    fixed_context: bool = True
    docs_dir: str | None = None


def get_store() -> SQLiteTraceStore:
    return SQLiteTraceStore(Path(os.getenv("AGENT_RELIABILITY_DB", "runs.db")))


def get_reports_dir() -> Path:
    return Path(os.getenv("AGENT_RELIABILITY_REPORTS_DIR", "reports"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/dashboard")
def dashboard() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.post("/agents/docs-qa/run")
def run_docs_qa(request: DocsQARunRequest) -> dict:
    agent = DocsQAAgent(docs_dir=request.docs_dir, llm_client=RuleBasedLLMClient(), store=get_store())
    return agent.answer(request.question)


@app.post("/agents/issue-triage/run")
def run_issue_triage(request: IssueTriageRunRequest) -> dict:
    agent = IssueTriageAgent(store=get_store())
    return agent.triage(title=request.title, body=request.body, repo=request.repo)


@app.get("/runs")
def list_runs(limit: int = 50) -> dict:
    store = get_store()
    store.init_schema()
    return {"runs": store.list_runs(limit=limit)}


@app.get("/reports/evals")
def list_eval_reports() -> dict:
    reports_dir = get_reports_dir()
    return {
        "reports_dir": str(reports_dir),
        "evals": [
            _load_eval_report(reports_dir / filename, key=key, label=label)
            for key, label, filename in EVAL_REPORTS
        ],
        "baseline": _load_baseline_report(reports_dir / "baseline-comparison.json"),
    }


@app.get("/runs/diff")
def diff_saved_runs(base_run_id: str, candidate_run_id: str) -> dict:
    try:
        return diff_runs(base_run_id=base_run_id, candidate_run_id=candidate_run_id, db_path=get_store().db_path)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/runs/{run_id}/replay")
def replay_saved_run(run_id: str, request: ReplayRunRequest) -> dict:
    try:
        return replay_run(
            run_id=run_id,
            db_path=get_store().db_path,
            fixed_context=request.fixed_context,
            docs_dir=request.docs_dir,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    store = get_store()
    store.init_schema()
    try:
        run = store.get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"run": run, "steps": store.list_steps(run_id)}


def _load_eval_report(path: Path, key: str, label: str) -> dict[str, Any]:
    payload = _read_json_file(path)
    if payload is None:
        return _unavailable_report(key=key, label=label, path=path)

    results = [_summarize_eval_case(result) for result in payload.get("results", [])]
    return {
        "key": key,
        "label": label,
        "path": str(path),
        "available": True,
        "generated_at": payload.get("generated_at"),
        "summary": payload.get("summary", _summarize_cases(results)),
        "results": results,
    }


def _load_baseline_report(path: Path) -> dict[str, Any]:
    payload = _read_json_file(path)
    if payload is None:
        return {
            "path": str(path),
            "available": False,
            "summary": {
                "baseline_total": 0,
                "candidate_total": 0,
                "shared": 0,
                "regressions": 0,
                "improvements": 0,
                "added": 0,
                "removed": 0,
            },
            "regressions": [],
            "improvements": [],
            "added": [],
            "removed": [],
        }

    return {
        "path": str(path),
        "available": True,
        "baseline_path": payload.get("baseline_path"),
        "candidate_path": payload.get("candidate_path"),
        "summary": payload.get("summary", {}),
        "regressions": payload.get("regressions", []),
        "improvements": payload.get("improvements", []),
        "added": payload.get("added", []),
        "removed": payload.get("removed", []),
    }


def _read_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _unavailable_report(key: str, label: str, path: Path) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "path": str(path),
        "available": False,
        "generated_at": None,
        "summary": {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0},
        "results": [],
    }


def _summarize_eval_case(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": result.get("case_id"),
        "agent": result.get("agent"),
        "passed": bool(result.get("passed")),
        "run_id": result.get("run_id"),
        "latency_ms": result.get("latency_ms"),
        "failed_checks": [
            check.get("name")
            for check in result.get("checks", [])
            if not check.get("passed")
        ],
    }


def _summarize_cases(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    failed = sum(1 for result in results if not result["passed"])
    passed = total - failed
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": 0.0 if total == 0 else passed / total,
    }
