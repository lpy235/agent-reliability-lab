# Replay And Diff Design

## Purpose

Replay and Diff turn stored agent runs into versioned engineering artifacts. After the MVP records Docs QA traces, this feature lets a user rerun a saved case and compare the original run with the replayed run.

## Scope

This phase implements:

- Replay a saved Docs QA run by `run_id`.
- Optionally reuse the original retrieved chunks as fixed replay context.
- Compare two stored runs.
- Write a Markdown diff report.
- Expose small CLI and FastAPI surfaces.
- Add static example artifacts for GitHub readers.

This phase does not implement dashboard UI, issue triage, real model comparison workflows, or CI artifact uploads.

## Replay Behavior

Replay reads a stored run from SQLite and extracts:

- `input.question`
- `input.docs_dir`
- original `retrieve_docs` chunks when fixed context is requested

Replay creates a new run with the same question. If fixed context is enabled, the Docs QA agent skips live retrieval and records a replay retrieval step using the saved chunks. The replay result includes:

- original `source_run_id`
- new `replay_run_id`
- whether fixed context was used
- answer, citations, grounded flag, latency, and retrieved chunks

## Diff Behavior

Run diff compares two stored runs:

- final answer text
- groundedness
- step path
- retrieved chunk IDs
- citation sources
- latency delta

The diff engine returns a JSON-friendly dictionary and can write `docs/examples/run-diff.md` or any report path.

## Public Interfaces

CLI:

```bash
python -m tracing.replay <run_id> --db-path runs.db --fixed-context
python -m tracing.diff <base_run_id> <candidate_run_id> --db-path runs.db --report-path reports/run-diff.md
```

API:

- `POST /runs/{run_id}/replay`
- `GET /runs/diff?base_run_id=...&candidate_run_id=...`

## Acceptance Criteria

- Replay creates a new stored run.
- Fixed-context replay uses the original retrieved chunks.
- Diff detects changed answers, retrieval chunk sets, step paths, groundedness, and latency deltas.
- Markdown diff report contains both run IDs and human-readable changed fields.
- Existing MVP tests still pass.

