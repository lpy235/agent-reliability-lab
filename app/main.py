from __future__ import annotations

import os
from pathlib import Path

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
