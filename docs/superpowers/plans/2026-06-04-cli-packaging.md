# CLI Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Agent Reliability Lab installable and expose core workflows as console scripts.

**Architecture:** Keep the existing flat package layout and add setuptools metadata in `pyproject.toml`. Reuse existing command `main()` functions and add one thin API launcher.

**Tech Stack:** Python packaging with setuptools, argparse, uvicorn, pytest.

---

## Tasks

- [ ] Add `pyproject.toml` with package metadata, dependencies, package data, and console scripts.
- [ ] Add `app/cli.py` to start `app.main:app` with host, port, database path, and reload options.
- [ ] Add tests that verify script metadata and the API launcher behavior without starting a server.
- [ ] Bundle demo documents and eval cases so default CLI commands work outside the repository root.
- [ ] Update GitHub Actions to install `.[dev]` and run `arl-harness`.
- [ ] Update README and the reusable workflow template to use packaged commands.
- [ ] Verify editable install, console script help output, pytest, harness, and GitHub Actions.
