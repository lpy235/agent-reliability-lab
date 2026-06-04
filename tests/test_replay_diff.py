from agents.docs_qa_agent import DocsQAAgent
from agents.llm import RuleBasedLLMClient
from tracing.diff import diff_runs, write_diff_report
from tracing.replay import replay_run
from tracing.store import SQLiteTraceStore


def test_replay_run_uses_fixed_context(tmp_path):
    db_path = tmp_path / "runs.db"
    store = SQLiteTraceStore(db_path)
    agent = DocsQAAgent(docs_dir="sample_docs", llm_client=RuleBasedLLMClient(), store=store)
    original = agent.answer("How do I configure the database?")

    replay = replay_run(original["run_id"], db_path=db_path, fixed_context=True)

    assert replay["source_run_id"] == original["run_id"]
    assert replay["replay_run_id"] != original["run_id"]
    assert replay["fixed_context"] is True
    assert replay["result"]["retrieved_chunks"] == original["retrieved_chunks"]
    steps = store.list_steps(replay["replay_run_id"])
    assert steps[0]["events"][0]["type"] == "replay_retrieval"


def test_diff_runs_reports_changed_answer_and_retrieval(tmp_path):
    db_path = tmp_path / "runs.db"
    store = SQLiteTraceStore(db_path)
    agent = DocsQAAgent(docs_dir="sample_docs", llm_client=RuleBasedLLMClient(), store=store)
    base = agent.answer("How do I configure the database?")
    candidate = agent.answer("How do I run the API server?")

    diff = diff_runs(base["run_id"], candidate["run_id"], db_path=db_path)

    assert diff["changed"] is True
    by_field = {item["field"]: item for item in diff["comparisons"]}
    assert by_field["answer"]["changed"] is True
    assert by_field["retrieved_chunk_ids"]["changed"] is True
    assert diff["latency"]["delta_ms"] is not None


def test_write_diff_report(tmp_path):
    db_path = tmp_path / "runs.db"
    report_path = tmp_path / "run-diff.md"
    store = SQLiteTraceStore(db_path)
    agent = DocsQAAgent(docs_dir="sample_docs", llm_client=RuleBasedLLMClient(), store=store)
    base = agent.answer("How do I configure the database?")
    candidate = replay_run(base["run_id"], db_path=db_path, fixed_context=True)["result"]
    diff = diff_runs(base["run_id"], candidate["run_id"], db_path=db_path)

    result = write_diff_report(diff, report_path)

    assert result["report_path"] == str(report_path)
    text = report_path.read_text(encoding="utf-8")
    assert "Agent Reliability Lab Run Diff" in text
    assert base["run_id"] in text
    assert candidate["run_id"] in text
