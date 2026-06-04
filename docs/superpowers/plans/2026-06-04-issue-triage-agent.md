# Issue Triage Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic dry-run GitHub issue triage agent with traceable simulated tool calls and eval coverage.

**Architecture:** Add `agents/issue_triage_agent.py`, extend eval metrics/runner for `issue_triage`, add sample JSONL cases, expose a FastAPI endpoint, and update `harness.py` plus README examples.

**Tech Stack:** Python, FastAPI, SQLite trace store, pytest, JSONL evals.

---

## Tasks

- [ ] Add `IssueTriageAgent` with deterministic label/priority rules.
- [ ] Record dry-run tool calls in trace steps.
- [ ] Extend `evals.metrics` and `evals.runner` for issue triage expectations.
- [ ] Add `evals/cases/issue_triage.jsonl`.
- [ ] Add API endpoint `POST /agents/issue-triage/run`.
- [ ] Update `harness.py` to include issue triage eval summary.
- [ ] Add tests for agent, eval runner, and API.
- [ ] Add README and static example updates.
- [ ] Run pytest, harness, and push.

