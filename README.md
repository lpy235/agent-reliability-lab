# Agent Reliability Lab

Agent Reliability Lab is a lightweight evaluation and observability toolkit for LLM agents. It makes agent behavior recordable, inspectable, and regression-testable instead of treating each run as a black box.

## Why This Exists

LLM agents often change behavior when prompts, models, tools, or retrieval data change. This project turns those changes into engineering signals:

- What did the agent retrieve?
- What prompt did it build?
- Which citations support the answer?
- Did the eval case pass or fail?
- How long did the run take?
- Can the same case be tested again later?

## Features

- Trace SDK for agent runs and intermediate steps
- SQLite-backed run and step storage
- Local-document Docs QA agent for RAG evaluation
- JSONL regression test suite
- Groundedness, citation, keyword, and latency checks
- Markdown eval reports for prompt and model changes
- FastAPI endpoints for manual run inspection
- GitHub Actions CI template for tests and the MVP harness

## Architecture

```text
sample_docs/ + question
        |
        v
DocsQAAgent
  - retrieve local chunks
  - build grounded prompt
  - generate deterministic answer
        |
        +--> Trace SDK --> SQLite runs.db
        |
        +--> JSONL eval runner --> Markdown report
        |
        +--> FastAPI endpoints for inspection
```

Core modules:

- `agents/`: retrieval, LLM clients, and Docs QA orchestration
- `tracing/`: trace models, SDK, and SQLite persistence
- `evals/`: JSONL case loading, metrics, report generation, and CLI runner
- `app/`: FastAPI endpoints
- `harness.py`: one-command MVP demo

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -v
python harness.py
```

The harness runs one sample Docs QA question, executes the JSONL eval suite, stores traces in `runs.db`, and writes a Markdown report to `reports/eval-report.md`.

## Quick Demo

Run the harness:

```bash
python harness.py
```

Expected summary shape:

```json
{
  "sample_run": {
    "answer": "Set `DATABASE_URL` in the environment before starting the service.",
    "grounded": true,
    "run_id": "run_..."
  },
  "eval": {
    "total": 2,
    "passed": 2,
    "failed": 0,
    "pass_rate": 1.0
  }
}
```

Static examples:

- [Sample Docs QA run](docs/examples/sample-run.json)
- [Sample eval report](docs/examples/eval-report.md)
- [GitHub Actions CI template](docs/examples/github-actions-ci.yml)

## Enable GitHub Actions

The CI template runs `pytest` and `harness.py`. To enable it in this repository, copy it into GitHub's workflow directory:

```bash
mkdir -p .github/workflows
cp docs/examples/github-actions-ci.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "ci: enable github actions"
git push
```

GitHub requires the pushing credential to have `workflow` permission for this step.

## Run JSONL Evals

```bash
python -m evals.runner evals/cases/docs_qa.jsonl \
  --docs-dir sample_docs \
  --db-path runs.db \
  --report-path reports/eval-report.md
```

The eval command exits with a nonzero status when any case fails, so it can be used in CI.

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

## What This Demonstrates

This project is not a chat demo. It demonstrates reliability engineering for tool-using and retrieval-augmented LLM agents:

- evaluation harness design
- trace and observability primitives
- regression testing for prompt and retrieval behavior
- inspectable RAG groundedness checks
- API and CLI surfaces over the same core agent logic

## Roadmap

- Replay saved runs with fixed inputs and retrieved context
- Diff two runs across output, retrieval, tool calls, latency, and eval status
- Add a compact dashboard for trace timeline inspection
- Add Issue Triage agent with simulated tool calls
- Add safety checks for PII, forbidden tools, and approval-required tools
- Add GitHub Actions report artifacts

## Project Documents

- [Project overview](Agent_Reliability_Lab_项目说明.md)
- [MVP design spec](docs/superpowers/specs/2026-06-04-agent-reliability-lab-mvp-design.md)
- [MVP implementation plan](docs/superpowers/plans/2026-06-04-agent-reliability-lab-mvp.md)
- [GitHub presentation and CI plan](docs/superpowers/plans/2026-06-04-github-presentation-ci.md)

## Tech Stack

- Python
- FastAPI
- SQLite
- pytest
- GitHub Actions
- OpenAI-compatible LLM API support

## Scope

The MVP focuses on agent reliability engineering: tracing, RAG evaluation, regression testing, and inspectable reports. It intentionally avoids private user-memory systems, proactive companion behavior, or unrelated personal-agent product concepts.

## License

MIT License.
