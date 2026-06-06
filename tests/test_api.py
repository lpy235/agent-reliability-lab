import json

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_and_static_assets():
    client = TestClient(app)

    dashboard_response = client.get("/dashboard")
    js_response = client.get("/static/app.js")
    css_response = client.get("/static/styles.css")

    assert dashboard_response.status_code == 200
    assert "Agent Reliability Lab" in dashboard_response.text
    assert js_response.status_code == 200
    assert "loadRuns" in js_response.text
    assert css_response.status_code == 200
    assert ".layout" in css_response.text


def test_docs_qa_run_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_RELIABILITY_DB", str(tmp_path / "runs.db"))
    client = TestClient(app)
    response = client.post("/agents/docs-qa/run", json={"question": "How do I configure the database?", "docs_dir": "sample_docs"})

    assert response.status_code == 200
    body = response.json()
    assert "DATABASE_URL" in body["answer"]
    assert body["run_id"].startswith("run_")


def test_issue_triage_run_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_RELIABILITY_DB", str(tmp_path / "runs.db"))
    client = TestClient(app)
    response = client.post(
        "/agents/issue-triage/run",
        json={
            "title": "App crashes when uploading large files",
            "body": "The upload page freezes after selecting a 2GB file.",
            "repo": {"name": "demo/app"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "bug"
    assert body["priority"] == "high"
    assert body["tool_calls"][0]["name"] == "search_similar_issues"


def test_run_inspection_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_RELIABILITY_DB", str(tmp_path / "runs.db"))
    client = TestClient(app)
    run_response = client.post("/agents/docs-qa/run", json={"question": "How do I configure the database?", "docs_dir": "sample_docs"})
    run_id = run_response.json()["run_id"]

    inspect_response = client.get(f"/runs/{run_id}")

    assert inspect_response.status_code == 200
    assert inspect_response.json()["run"]["run_id"] == run_id
    assert len(inspect_response.json()["steps"]) == 2


def test_replay_and_diff_endpoints(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_RELIABILITY_DB", str(tmp_path / "runs.db"))
    client = TestClient(app)
    run_response = client.post("/agents/docs-qa/run", json={"question": "How do I configure the database?", "docs_dir": "sample_docs"})
    run_id = run_response.json()["run_id"]

    replay_response = client.post(f"/runs/{run_id}/replay", json={"fixed_context": True})

    assert replay_response.status_code == 200
    replay_body = replay_response.json()
    assert replay_body["source_run_id"] == run_id
    assert replay_body["fixed_context"] is True

    diff_response = client.get(
        "/runs/diff",
        params={"base_run_id": run_id, "candidate_run_id": replay_body["replay_run_id"]},
    )

    assert diff_response.status_code == 200
    diff_body = diff_response.json()
    assert diff_body["base_run_id"] == run_id
    assert diff_body["candidate_run_id"] == replay_body["replay_run_id"]
    assert "comparisons" in diff_body


def test_reports_endpoint_handles_missing_files(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_RELIABILITY_REPORTS_DIR", str(tmp_path / "reports"))
    client = TestClient(app)

    response = client.get("/reports/evals")

    assert response.status_code == 200
    body = response.json()
    assert body["evals"][0]["available"] is False
    assert body["evals"][1]["available"] is False
    assert body["baseline"]["available"] is False


def test_reports_endpoint_reads_eval_and_baseline_json(tmp_path, monkeypatch):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    monkeypatch.setenv("AGENT_RELIABILITY_REPORTS_DIR", str(reports_dir))
    (reports_dir / "eval-report.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-06-06T00:00:00+00:00",
                "summary": {"total": 1, "passed": 0, "failed": 1, "pass_rate": 0.0},
                "results": [
                    {
                        "case_id": "docs_database_url",
                        "agent": "docs_qa",
                        "passed": False,
                        "run_id": "run_docs",
                        "latency_ms": 42,
                        "checks": [
                            {"name": "required_keyword:DATABASE_URL", "passed": False},
                            {"name": "max_latency_ms", "passed": True},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports_dir / "issue-triage-report.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-06-06T00:00:01+00:00",
                "summary": {"total": 1, "passed": 1, "failed": 0, "pass_rate": 1.0},
                "results": [
                    {
                        "case_id": "issue_crash",
                        "agent": "issue_triage",
                        "passed": True,
                        "run_id": "run_issue",
                        "latency_ms": 12,
                        "checks": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports_dir / "baseline-comparison.json").write_text(
        json.dumps(
            {
                "baseline_path": "baselines/docs_qa_eval_report.json",
                "candidate_path": "reports/eval-report.json",
                "summary": {
                    "baseline_total": 1,
                    "candidate_total": 1,
                    "shared": 1,
                    "regressions": 1,
                    "improvements": 0,
                    "added": 0,
                    "removed": 0,
                },
                "regressions": [{"case_id": "docs_database_url"}],
                "improvements": [],
                "unchanged": [],
                "added": [],
                "removed": [],
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(app)

    response = client.get("/reports/evals")

    assert response.status_code == 200
    body = response.json()
    assert body["evals"][0]["available"] is True
    assert body["evals"][0]["results"][0]["failed_checks"] == ["required_keyword:DATABASE_URL"]
    assert body["evals"][1]["summary"]["pass_rate"] == 1.0
    assert body["baseline"]["summary"]["regressions"] == 1
