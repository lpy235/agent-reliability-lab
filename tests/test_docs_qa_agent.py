from agents.docs_qa_agent import DocsQAAgent
from agents.llm import RuleBasedLLMClient
from agents.retrieval import retrieve_chunks
from tracing.store import SQLiteTraceStore


def test_retrieval_finds_database_config():
    chunks = retrieve_chunks("How do I configure the database?", docs_dir="sample_docs", top_k=2)
    assert chunks
    assert chunks[0]["source"] == "sample_docs/config.md"
    assert "DATABASE_URL" in chunks[0]["text"]


def test_retrieval_finds_api_deployment():
    chunks = retrieve_chunks("How do I run the API server?", docs_dir="sample_docs", top_k=2)
    assert chunks
    assert chunks[0]["source"] == "sample_docs/deployment.md"
    assert "uvicorn" in chunks[0]["text"]


def test_rule_based_llm_uses_context():
    client = RuleBasedLLMClient()
    response = client.complete("Question: How do I configure the database?\nContext:\nSet DATABASE_URL in the environment.")
    assert "DATABASE_URL" in response.text
    assert response.tokens["total"] > 0


def test_docs_qa_agent_records_trace(tmp_path):
    store = SQLiteTraceStore(tmp_path / "runs.db")
    agent = DocsQAAgent(docs_dir="sample_docs", llm_client=RuleBasedLLMClient(), store=store)

    result = agent.answer("How do I configure the database?")

    assert "DATABASE_URL" in result["answer"]
    assert result["citations"][0]["source"] == "sample_docs/config.md"
    assert result["grounded"] is True
    assert result["run_id"].startswith("run_")
    steps = store.list_steps(result["run_id"])
    assert [step["name"] for step in steps] == ["retrieve_docs", "generate_answer"]
