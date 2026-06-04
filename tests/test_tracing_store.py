from tracing.models import RunRecord, StepRecord
from tracing.sdk import Trace
from tracing.store import SQLiteTraceStore


def test_store_creates_and_reads_run(tmp_path):
    store = SQLiteTraceStore(tmp_path / "runs.db")
    store.init_schema()
    run = RunRecord.start(agent_name="docs_qa", input={"question": "How do I configure the database?"})

    store.create_run(run)
    store.update_run(run.run_id, status="success", output={"answer": "Use DATABASE_URL."}, metrics={"latency_ms": 12})

    saved = store.get_run(run.run_id)
    assert saved["run_id"] == run.run_id
    assert saved["status"] == "success"
    assert saved["input"]["question"] == "How do I configure the database?"
    assert saved["output"]["answer"] == "Use DATABASE_URL."
    assert saved["metrics"]["latency_ms"] == 12


def test_store_creates_updates_and_lists_steps(tmp_path):
    store = SQLiteTraceStore(tmp_path / "runs.db")
    store.init_schema()
    run = RunRecord.start(agent_name="docs_qa", input={"question": "Q"})
    step = StepRecord.start(run_id=run.run_id, name="retrieve_docs")
    step.events.append({"type": "retrieval", "chunks": [{"source": "sample_docs/config.md"}]})
    step.finish(state_after={"chunk_count": 1}, decision={"next_action": "generate_answer"}, reason_tags=["chunks_found"])

    store.create_run(run)
    store.create_step(step)
    step.tokens = {"total": 10}
    store.update_step(step)

    steps = store.list_steps(run.run_id)
    assert len(steps) == 1
    assert steps[0]["name"] == "retrieve_docs"
    assert steps[0]["events"][0]["type"] == "retrieval"
    assert steps[0]["reason_tags"] == ["chunks_found"]
    assert steps[0]["tokens"]["total"] == 10


def test_trace_context_records_step(tmp_path):
    store = SQLiteTraceStore(tmp_path / "runs.db")
    store.init_schema()
    trace = Trace.start(store=store, agent_name="docs_qa", input={"question": "Q"})

    with trace.step("retrieve_docs") as step:
        step.log_state(before={"question": "Q"})
        step.log_event({"type": "retrieval", "chunks": [{"chunk_id": "config.md#0"}]})
        step.log_decision({"next_action": "generate_answer", "reason_tags": ["chunks_found"]})
        step.log_state(after={"chunk_count": 1})

    trace.finish(output={"answer": "A"}, status="success", metrics={"latency_ms": 5})

    saved = store.get_run(trace.run_id)
    steps = store.list_steps(trace.run_id)
    assert saved["status"] == "success"
    assert steps[0]["state_before"]["question"] == "Q"
    assert steps[0]["state_after"]["chunk_count"] == 1
    assert steps[0]["decision"]["next_action"] == "generate_answer"
