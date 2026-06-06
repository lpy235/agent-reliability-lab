# Changelog

All notable changes to Agent Reliability Lab are documented in this file.

## Unreleased

### Added

- `arl-dashboard` CLI for opening saved CI artifacts with explicit `runs.db` and reports paths.
- Issue Triage baseline gate in CI using `baselines/issue_triage_eval_report.json`.
- Dashboard baseline selector for switching between Docs QA and Issue Triage comparisons.
- README instructions for inspecting `agent-reliability-lab-reports` artifacts locally.

## v0.2.0 - 2026-06-06

### Added

- GitHub Actions artifact upload for Markdown eval reports and `runs.db`.
- JSON eval reports for baseline comparison.
- `arl-baseline` CLI for comparing eval reports and flagging regressions.
- Docs QA baseline gate in CI.
- JSON baseline comparison reports for CI artifacts and dashboard consumption.
- Dashboard Reports view for eval summaries, case results, and baseline changes.

## v0.1.0 - 2026-06-05

Initial public release.

### Added

- Trace SDK for recording agent runs, intermediate steps, events, decisions, token usage, cost, latency, status, and errors.
- SQLite-backed run storage with APIs for creating, listing, reading, and inspecting saved runs.
- Docs QA demo agent for local-document RAG reliability checks.
- Deterministic rule-based LLM client for reproducible local demos and CI runs.
- JSONL eval runner for Docs QA and Issue Triage cases.
- Markdown eval reports with pass/fail summaries and per-check details.
- Groundedness, citation, keyword, forbidden-keyword, latency, and safety-oriented eval checks.
- Saved-run replay with fixed retrieved context.
- Run-to-run diff reports for answers, groundedness, step paths, retrieved chunks, citations, and latency.
- Dry-run Issue Triage agent with deterministic labels, priorities, next actions, and simulated tool calls.
- PII redaction and tool policy checks for issue triage inputs and dry-run tool calls.
- FastAPI endpoints for running agents, listing runs, inspecting traces, replaying runs, and diffing runs.
- Framework-free dashboard for run inspection, trace timelines, output review, replay, and diff.
- Dashboard screenshot for the GitHub README.
- Python packaging metadata in `pyproject.toml`.
- Console scripts: `arl-harness`, `arl-eval`, `arl-replay`, `arl-diff`, and `arl-api`.
- Bundled demo docs and eval cases so the default CLI demo can run outside the repository root.
- GitHub Actions CI for tests and the harness.

### Known Limitations

- The included agents are deterministic demos, not production issue-triage or RAG systems.
- The dashboard is a local inspection workbench and does not include authentication.
- The safety layer is intentionally lightweight and focuses on observable redaction and tool-policy checks.
- Real GitHub issue mutation is not enabled; issue triage records dry-run tool calls only.
- Workflow updates require a GitHub credential with `workflow` scope when pushed from the command line.
