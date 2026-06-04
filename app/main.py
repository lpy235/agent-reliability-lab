from __future__ import annotations

import os
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
    return SQLiteTraceStore(Path(os.getenv("AGENT_RELIABILITY_DB", "runs.db")))


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
