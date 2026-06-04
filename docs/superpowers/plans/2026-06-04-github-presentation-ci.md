# GitHub Presentation And CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the MVP repository easier to trust at a glance by adding CI verification, example artifacts, and stronger README presentation.

**Architecture:** This change does not alter agent behavior. It adds repository-level automation under `.github/workflows/`, static examples under `docs/examples/`, and README sections that point users to the runnable harness and inspectable outputs.

**Tech Stack:** GitHub Actions, Python, pytest, Markdown, JSON.

---

## Tasks

- [ ] Add `.github/workflows/ci.yml` to install dependencies, run `pytest`, and run `harness.py`.
- [ ] Add `docs/examples/sample-run.json` showing a representative Docs QA output.
- [ ] Add `docs/examples/eval-report.md` showing the Markdown report shape without committing generated runtime reports.
- [ ] Update `README.md` with CI badge, architecture, quick demo, example output links, and roadmap.
- [ ] Run `.venv/bin/python -m pytest -v` and `.venv/bin/python harness.py`.
- [ ] Commit and push the presentation polish.

