# Safety And Tool Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add lightweight PII redaction and tool policy checks to make safety behavior visible in traces and evals.

**Architecture:** Add a focused `safety` package, integrate it into `IssueTriageAgent`, extend eval metrics for safety expectations, and add sample cases/docs.

**Tech Stack:** Python, pytest, JSONL evals.

---

## Tasks

- [ ] Add `safety/pii_redactor.py`.
- [ ] Add `safety/tool_policy.py`.
- [ ] Integrate redaction and policy checks into Issue Triage.
- [ ] Extend issue triage eval metrics with safety checks.
- [ ] Add tests and sample safety eval cases.
- [ ] Update README and examples.
- [ ] Run pytest, harness, issue eval, commit, and push.

