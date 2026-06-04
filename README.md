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
- Dry-run Issue Triage agent with simulated tool calls
- JSONL regression test suite
- Groundedness, citation, keyword, and latency checks
- PII redaction and dry-run tool policy checks
- Markdown eval reports for prompt and model changes
- Saved-run replay with fixed retrieved context
- Run-to-run diff reports for answer, retrieval, steps, citations, and latency
- FastAPI endpoints for manual run inspection
- GitHub Actions CI template for tests and the MVP harness

## Architecture

```text
sample_docs/ + question
        |
        v
DocsQAAgent / IssueTriageAgent
  - retrieve local chunks or analyze issue text
  - build grounded prompt or simulate dry-run tool calls
  - generate deterministic answer or triage decision
        |
        +--> Trace SDK --> SQLite runs.db
        |
        +--> JSONL eval runner --> Markdown report
        |
        +--> Replay + Diff --> Markdown diff report
        |
        +--> FastAPI endpoints for inspection
```

Core modules:

- `agents/`: retrieval, LLM clients, and Docs QA orchestration
- `agents/issue_triage_agent.py`: deterministic issue triage and dry-run tool calls
- `tracing/`: trace models, SDK, and SQLite persistence
- `safety/`: PII redaction and tool policy checks
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
  },
  "issue_triage_eval": {
    "total": 3,
    "passed": 3,
    "failed": 0,
    "pass_rate": 1.0
  }
}
```

Static examples:

- [Sample Docs QA run](docs/examples/sample-run.json)
- [Sample issue triage run](docs/examples/issue-triage-run.json)
- [Sample eval report](docs/examples/eval-report.md)
- [Sample run diff](docs/examples/run-diff.md)
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

Run the issue triage eval suite:

```bash
python -m evals.runner evals/cases/issue_triage.jsonl \
  --db-path runs.db \
  --report-path reports/issue-triage-report.md
```

Issue triage evals can assert required tool calls, forbidden tool calls, PII redaction, approval-required tools, and maximum safety violations.

## Replay And Diff Runs

Replay a saved run with its original retrieved chunks:

```bash
python -m tracing.replay <run_id> --db-path runs.db
```

Compare two saved runs and write a Markdown report:

```bash
python -m tracing.diff <base_run_id> <candidate_run_id> \
  --db-path runs.db \
  --report-path reports/run-diff.md
```

Replay is useful when you want to rerun the same input while controlling retrieval context. Diff is useful when a prompt, model, or docs change and you need to see which behavior actually moved.

## Run Docs QA Through The API

```bash
uvicorn app.main:app --reload
```

In another shell:

```bash
curl -X POST http://127.0.0.1:8000/agents/docs-qa/run \
  -H "Content-Type: application/json" \
  -d '{"question":"How do I configure the database?","docs_dir":"sample_docs"}'
curl -X POST http://127.0.0.1:8000/agents/issue-triage/run \
  -H "Content-Type: application/json" \
  -d '{"title":"App crashes when uploading large files","body":"The upload page freezes after selecting a 2GB file."}'
```

Inspect saved runs:

```bash
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/runs/<run_id>
curl -X POST http://127.0.0.1:8000/runs/<run_id>/replay \
  -H "Content-Type: application/json" \
  -d '{"fixed_context":true}'
curl "http://127.0.0.1:8000/runs/diff?base_run_id=<run_id>&candidate_run_id=<run_id>"
```

## What This Demonstrates

This project is not a chat demo. It demonstrates reliability engineering for tool-using and retrieval-augmented LLM agents:

- evaluation harness design
- trace and observability primitives
- regression testing for prompt and retrieval behavior
- replay and diff workflows for saved agent behavior
- dry-run tool-call reliability checks for issue triage
- lightweight safety checks for PII and tool policy violations
- inspectable RAG groundedness checks
- API and CLI surfaces over the same core agent logic

## Roadmap

- Add a compact dashboard for trace timeline inspection
- Add GitHub Actions report artifacts

## Project Documents

- [Project overview](Agent_Reliability_Lab_项目说明.md)
- [MVP design spec](docs/superpowers/specs/2026-06-04-agent-reliability-lab-mvp-design.md)
- [MVP implementation plan](docs/superpowers/plans/2026-06-04-agent-reliability-lab-mvp.md)
- [GitHub presentation and CI plan](docs/superpowers/plans/2026-06-04-github-presentation-ci.md)
- [Issue Triage Agent design](docs/superpowers/specs/2026-06-04-issue-triage-agent-design.md)

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
