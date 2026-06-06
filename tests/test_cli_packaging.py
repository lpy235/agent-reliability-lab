from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from app import cli
from harness import run_harness


def test_pyproject_defines_console_scripts():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["name"] == "agent-reliability-lab"
    assert metadata["project"]["scripts"] == {
        "arl-api": "app.cli:main",
        "arl-baseline": "evals.baseline:main",
        "arl-dashboard": "app.cli:dashboard_main",
        "arl-diff": "tracing.diff:main",
        "arl-eval": "evals.runner:main",
        "arl-harness": "harness:main",
        "arl-replay": "tracing.replay:main",
    }


def test_api_cli_sets_db_path_and_runs_uvicorn(monkeypatch):
    calls = []

    def fake_run(app_path, host, port, reload):
        calls.append({"app_path": app_path, "host": host, "port": port, "reload": reload})

    monkeypatch.setattr(cli.uvicorn, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["arl-api", "--host", "0.0.0.0", "--port", "8765", "--db-path", "tmp-runs.db", "--reload"],
    )

    exit_code = cli.main()

    assert exit_code == 0
    assert calls == [{"app_path": "app.main:app", "host": "0.0.0.0", "port": 8765, "reload": True}]
    assert cli.os.environ["AGENT_RELIABILITY_DB"] == "tmp-runs.db"


def test_dashboard_cli_sets_db_and_reports_paths(monkeypatch):
    calls = []

    def fake_run(app_path, host, port, reload):
        calls.append({"app_path": app_path, "host": host, "port": port, "reload": reload})

    monkeypatch.setattr(cli.uvicorn, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "arl-dashboard",
            "--host",
            "0.0.0.0",
            "--port",
            "8766",
            "--db-path",
            "artifact/runs.db",
            "--reports-dir",
            "artifact/reports",
        ],
    )

    exit_code = cli.dashboard_main()

    assert exit_code == 0
    assert calls == [{"app_path": "app.main:app", "host": "0.0.0.0", "port": 8766, "reload": False}]
    assert cli.os.environ["AGENT_RELIABILITY_DB"] == "artifact/runs.db"
    assert cli.os.environ["AGENT_RELIABILITY_REPORTS_DIR"] == "artifact/reports"


def test_harness_resolves_bundled_demo_files_outside_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = run_harness(
        question="How do I configure the database?",
        docs_dir="sample_docs",
        cases_path="evals/cases/docs_qa.jsonl",
        issue_cases_path="evals/cases/issue_triage.jsonl",
        db_path="runs.db",
        report_path="eval-report.md",
        issue_report_path="issue-report.md",
    )

    assert result["eval"]["failed"] == 0
    assert result["issue_triage_eval"]["failed"] == 0
    assert Path("eval-report.md").exists()
