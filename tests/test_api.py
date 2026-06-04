from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


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
