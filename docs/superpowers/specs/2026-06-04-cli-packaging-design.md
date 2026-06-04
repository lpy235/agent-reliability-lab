# CLI Packaging Design

## Purpose

This phase makes Agent Reliability Lab installable as a Python project and exposes the main workflows as stable command-line entry points.

## Scope

This phase implements:

- `pyproject.toml` with project metadata, dependencies, optional dev dependencies, package data, and console scripts.
- `arl-harness` for the demo harness.
- `arl-eval` for JSONL eval runs.
- `arl-replay` for saved-run replay.
- `arl-diff` for run comparison.
- `arl-api` for starting the FastAPI API and dashboard.
- README and CI updates that use the packaged commands.
- Bundled demo documents and JSONL eval cases so default CLI commands work outside the repository root.

This phase does not rename the existing top-level packages, publish to PyPI, or add generated release artifacts.

## Architecture

The package keeps the current repository layout to avoid a risky source tree migration. Console scripts point at existing `main()` functions where they already exist. The API command uses a small wrapper in `app/cli.py` so users can configure host, port, database path, and reload mode without remembering the uvicorn import string.

## Acceptance Criteria

- `python -m pip install -e ".[dev]"` installs the project.
- `arl-harness`, `arl-eval`, `arl-replay`, `arl-diff`, and `arl-api --help` are available after install.
- `arl-harness` can run from a directory outside the repository by resolving bundled demo files.
- CI installs the editable package with dev dependencies.
- README documents the packaged workflow.
- Existing tests and harness verification continue to pass.
