# Agent Reliability Lab

Agent Reliability Lab is a lightweight evaluation and observability toolkit for LLM agents. It focuses on making agent behavior recordable, inspectable, and regression-testable instead of treating each run as a black box.

## Features

- Structured traces for agent runs and intermediate steps
- SQLite-backed run storage
- Local-document Docs QA agent for RAG evaluation
- JSONL regression test cases
- RAG groundedness and citation checks
- Markdown eval reports for prompt and model changes
- FastAPI endpoints for manual run inspection

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -v
python harness.py
```

The harness runs one sample Docs QA question, executes the JSONL eval suite, stores traces in `runs.db`, and writes a Markdown report to `reports/eval-report.md`.

## Run Docs QA Through The API

```bash
uvicorn app.main:app --reload
```

In another shell:

```bash
curl -X POST http://127.0.0.1:8000/agents/docs-qa/run \
  -H "Content-Type: application/json" \
  -d '{"question":"How do I configure the database?","docs_dir":"sample_docs"}'
```

Inspect saved runs:

```bash
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/runs/<run_id>
```

## Run JSONL Evals

```bash
python -m evals.runner evals/cases/docs_qa.jsonl \
  --docs-dir sample_docs \
  --db-path runs.db \
  --report-path reports/eval-report.md
```

The eval command exits with a nonzero status when any case fails, so it can be used in CI later.

## Current Status

The first MVP is implemented: a deterministic Docs QA agent, trace SDK, SQLite store, JSONL eval harness, Markdown report writer, pytest suite, and FastAPI inspection endpoints.

## Project Documents

- [Project overview](Agent_Reliability_Lab_项目说明.md)
- [MVP design spec](docs/superpowers/specs/2026-06-04-agent-reliability-lab-mvp-design.md)
- [MVP implementation plan](docs/superpowers/plans/2026-06-04-agent-reliability-lab-mvp.md)

## Tech Stack

- Python
- FastAPI
- SQLite
- pytest
- OpenAI-compatible LLM API support

## License

MIT License.

## Scope

The MVP focuses on agent reliability engineering: tracing, RAG evaluation, regression testing, and inspectable reports. It intentionally avoids private user-memory systems, proactive companion behavior, or unrelated personal-agent product concepts.
