from agents.issue_triage_agent import IssueTriageAgent
from tracing.store import SQLiteTraceStore


def test_issue_triage_classifies_bug_and_records_tool_calls(tmp_path):
    store = SQLiteTraceStore(tmp_path / "runs.db")
    agent = IssueTriageAgent(store=store)

    result = agent.triage(
        title="App crashes when uploading large files",
        body="The upload page freezes after selecting a 2GB file.",
        repo={"name": "demo/app"},
    )

    assert result["label"] == "bug"
    assert result["priority"] == "high"
    assert result["next_action"] == "dry_run_assign_label:bug"
    assert [tool["name"] for tool in result["tool_calls"]] == ["search_similar_issues", "infer_owner", "assign_label"]
    steps = store.list_steps(result["run_id"])
    assert [step["name"] for step in steps] == ["analyze_issue", "search_similar_issues", "infer_owner", "assign_label"]
    assert steps[1]["events"][0]["type"] == "tool_call"


def test_issue_triage_classifies_docs_as_low_priority(tmp_path):
    store = SQLiteTraceStore(tmp_path / "runs.db")
    agent = IssueTriageAgent(store=store)

    result = agent.triage(title="README typo in configuration example", body="Small docs typo.")

    assert result["label"] == "docs"
    assert result["priority"] == "low"
