# Agent Reliability Lab MVP Design

## Purpose

Agent Reliability Lab is a lightweight evaluation and observability toolkit for LLM agents. The MVP turns a simple Docs QA agent into an inspectable engineering object: each run is recorded, evaluated, and reported so prompt or model changes can be tested instead of guessed.

This first spec covers the smallest useful vertical slice:

- Run a local-document QA agent from a CLI and API.
- Record structured traces for retrieval and answer generation.
- Store runs and steps in SQLite.
- Evaluate runs from JSONL cases.
- Produce a Markdown report with pass/fail details.

The MVP does not include Issue Triage, Replay, Diff, Dashboard, GitHub Actions, OpenTelemetry, LangChain, or LlamaIndex. Those remain later phases.

## Recommended Approach

Use a plain Python package with focused modules and minimal dependencies.

Alternative approaches considered:

- Full web-first app with dashboard early. This is attractive for screenshots, but it risks spending the MVP on UI before trace and eval semantics are solid.
- Framework-heavy agent stack using LangChain or LlamaIndex. This speeds up some RAG pieces, but it hides the behavior this project is meant to observe.
- Minimal Python core with FastAPI endpoints and CLI runner. This is the recommended approach because it makes the reliability layer explicit, testable, and easy to explain in a resume or interview.

## Architecture

The MVP has four layers:

1. Agent layer: `DocsQAAgent` loads local markdown/txt documents, retrieves relevant chunks, builds a grounded prompt, and returns an answer with citations.
2. Tracing layer: a small SDK records run metadata and step-level state/event/decision information.
3. Persistence layer: a SQLite-backed store saves runs and trace steps as JSON-friendly records.
4. Evaluation layer: a JSONL runner executes cases, checks expectations, and writes a Markdown report.

FastAPI exposes the same core behavior for manual inspection, while the CLI is the main path for repeatable evals.

## Project Structure

```text
agent-reliability-lab/
  agents/
    __init__.py
    docs_qa_agent.py
    retrieval.py
    llm.py
  tracing/
    __init__.py
    sdk.py
    store.py
    models.py
  evals/
    __init__.py
    cases/
      docs_qa.jsonl
    runner.py
    metrics.py
    report.py
  app/
    __init__.py
    main.py
  sample_docs/
    config.md
    deployment.md
    troubleshooting.md
  reports/
    .gitkeep
  tests/
    test_tracing_store.py
    test_docs_qa_agent.py
    test_eval_runner.py
  README.md
  requirements.txt
```

The actual repository may use this layout directly because there is no existing codebase yet.

## Component Design

### Docs QA Agent

`DocsQAAgent` accepts:

- `docs_dir`: local directory containing `.md` and `.txt` files.
- `llm_client`: object with `complete(prompt: str) -> LLMResponse`.
- `trace`: optional trace object created by the SDK.

It returns a `DocsQAResult`:

```python
{
  "question": "How do I configure the database?",
  "answer": "Set DATABASE_URL in the environment...",
  "citations": [{"source": "sample_docs/config.md", "chunk_id": "config.md#0"}],
  "retrieved_chunks": [...],
  "grounded": true,
  "latency_ms": 123
}
```

Retrieval is intentionally simple in the MVP:

- Load markdown/txt files from `docs_dir`.
- Split by paragraph or heading-aware blocks.
- Score chunks using lowercase token overlap with the question.
- Return the top 3 chunks.

The first LLM client should support two modes:

- `RuleBasedLLMClient` for deterministic tests and local demos without API keys.
- `OpenAICompatibleClient` for real model calls when `OPENAI_API_KEY` and `OPENAI_BASE_URL` are configured.

If no API key is present, the CLI and API use the rule-based client by default.

### Tracing SDK

The SDK should support this public shape:

```python
store = SQLiteTraceStore("runs.db")
trace = Trace.start(store=store, agent_name="docs_qa", input={"question": question})

with trace.step("retrieve_docs") as step:
    step.log_state(before={"question": question})
    step.log_event({"type": "retrieval", "chunks": chunks})
    step.log_decision({"next_action": "generate_answer", "reason_tags": ["chunks_found"]})
    step.log_state(after={"chunk_count": len(chunks)})

trace.finish(output=result, status="success", metrics={"latency_ms": latency})
```

Each trace step records:

- `run_id`
- `step_id`
- `name`
- `state_before`
- `events`
- `decision`
- `reason_tags`
- `state_after`
- `started_at`
- `ended_at`
- `latency_ms`
- `tokens`
- `cost`

The SDK should still record failed runs by calling `trace.finish(status="error", error=...)`.

### SQLite Store

SQLite stores two tables:

`runs`:

- `run_id TEXT PRIMARY KEY`
- `agent_name TEXT NOT NULL`
- `status TEXT NOT NULL`
- `input_json TEXT NOT NULL`
- `output_json TEXT`
- `metrics_json TEXT`
- `error TEXT`
- `started_at TEXT NOT NULL`
- `ended_at TEXT`

`steps`:

- `step_id TEXT PRIMARY KEY`
- `run_id TEXT NOT NULL`
- `name TEXT NOT NULL`
- `state_before_json TEXT`
- `events_json TEXT`
- `decision_json TEXT`
- `reason_tags_json TEXT`
- `state_after_json TEXT`
- `tokens_json TEXT`
- `cost REAL`
- `started_at TEXT NOT NULL`
- `ended_at TEXT`
- `latency_ms INTEGER`

The store exposes:

- `init_schema()`
- `create_run(run)`
- `update_run(run_id, ...)`
- `create_step(step)`
- `update_step(step_id, ...)`
- `get_run(run_id)`
- `list_runs(limit=50)`
- `list_steps(run_id)`

### JSONL Eval Runner

The runner reads `evals/cases/docs_qa.jsonl`, executes each case, and evaluates expectations.

Supported expectations for MVP:

- `required_citations`: every listed path must appear in citations.
- `required_keywords`: each keyword must appear in the answer.
- `forbidden_keywords`: no forbidden keyword may appear in the answer.
- `max_latency_ms`: run latency must not exceed the limit.
- `grounded`: expected boolean, default `true` for docs QA cases.

Each case result includes:

- `case_id`
- `agent`
- `run_id`
- `passed`
- `checks`
- `latency_ms`
- `answer`
- `citations`

### Markdown Report

The report writer creates `reports/eval-report.md` with:

- timestamp
- total cases
- passed/failed count
- pass rate
- per-case table
- failure details with check names and actual values
- linked or printed `run_id` values for debugging

### FastAPI

FastAPI is a thin wrapper over the same core code.

Endpoints:

- `GET /health`
- `POST /agents/docs-qa/run`
- `GET /runs`
- `GET /runs/{run_id}`

The API is for manual verification and later dashboard support, not the primary eval path.

## Data Flow

Docs QA CLI/API run:

1. Receive question and docs directory.
2. Start trace run with agent name and input.
3. Retrieve chunks inside `retrieve_docs` step.
4. Generate answer inside `generate_answer` step.
5. Compute groundedness by checking that required citations come from retrieved chunks.
6. Finish trace with output and metrics.
7. Return answer, citations, grounded flag, and run ID.

Eval run:

1. Load JSONL cases.
2. For each case, run `DocsQAAgent`.
3. Apply metric checks.
4. Save traces through SQLite.
5. Write Markdown report.
6. Exit with nonzero status if any case fails, so CI can use it later.

## Error Handling

- Missing docs directory: fail fast with a clear message.
- Empty docs directory: run records an error and eval case fails.
- Invalid JSONL line: runner reports file path and line number, then exits nonzero.
- LLM API failure: trace run finishes with `status="error"` and includes the error string.
- Store failure: raise the original exception; the MVP does not need retry logic.

## Testing Strategy

Tests should run without network access or API keys.

Required tests:

- SQLite schema initialization creates `runs` and `steps`.
- Trace SDK records a run with one step and can read it back.
- Docs QA retrieval returns the expected sample doc for a known question.
- Docs QA deterministic client returns an answer with citations.
- Eval runner marks a passing case as passed.
- Eval runner marks missing required keyword or citation as failed.
- Invalid JSONL produces a useful error.

The first implementation plan should use pytest and deterministic fixtures.

## README Requirements

README should include:

- Project positioning in one paragraph.
- Quick start commands.
- Example Docs QA command.
- Example eval command.
- Short explanation of trace, eval, and report concepts.
- A small sample report table.

Screenshots, dashboard images, GitHub Actions badge, replay, and diff examples are deferred until later phases.

## Acceptance Criteria

The MVP is complete when:

- `pytest` passes locally.
- A user can run a Docs QA question against `sample_docs`.
- A SQLite database contains the run and trace steps.
- `python -m evals.runner evals/cases/docs_qa.jsonl` produces `reports/eval-report.md`.
- The eval command exits nonzero when a case fails.
- FastAPI can start and expose health, run, and run-inspection endpoints.

## Out of Scope

- Issue Triage Agent.
- Real GitHub API writes.
- Replay.
- Run diff.
- Dashboard UI.
- CI workflow.
- PII redaction and tool policy checks.
- Multi-agent benchmarks.
- Private user memory, proactive companion behavior, or any product-specific personal agent details.

