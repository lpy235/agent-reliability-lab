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


def test_run_inspection_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_RELIABILITY_DB", str(tmp_path / "runs.db"))
    client = TestClient(app)
    run_response = client.post("/agents/docs-qa/run", json={"question": "How do I configure the database?", "docs_dir": "sample_docs"})
    run_id = run_response.json()["run_id"]

    inspect_response = client.get(f"/runs/{run_id}")

    assert inspect_response.status_code == 200
    assert inspect_response.json()["run"]["run_id"] == run_id
    assert len(inspect_response.json()["steps"]) == 2
