# Replay And Diff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add saved-run replay and run-to-run diff for Docs QA traces.

**Architecture:** Extend `DocsQAAgent.answer()` with an optional retrieved-chunk override, add `tracing/replay.py` for replay orchestration, add `tracing/diff.py` for JSON and Markdown diffs, then expose both through focused tests, CLI entrypoints, API endpoints, README, and static examples.

**Tech Stack:** Python, SQLite, FastAPI, pytest, Markdown.

---

## Tasks

- [ ] Add tests for fixed-context replay and run diff.
- [ ] Extend `DocsQAAgent.answer()` to accept fixed retrieved chunks.
- [ ] Implement `tracing/replay.py` with `replay_run()` and CLI.
- [ ] Implement `tracing/diff.py` with `diff_runs()`, `write_diff_report()`, and CLI.
- [ ] Add FastAPI endpoints for replay and diff.
- [ ] Add example `docs/examples/run-diff.md`.
- [ ] Update README with Replay/Diff usage.
- [ ] Run pytest, replay CLI, diff CLI, and harness before committing.

