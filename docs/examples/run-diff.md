# Agent Reliability Lab Run Diff

Base run: `run_example_docs_qa_001`
Candidate run: `run_example_docs_qa_002`
Changed: `true`

## Field Changes

| Field | Changed | Before | After |
| --- | --- | --- | --- |
| answer | true | <code>"Set `DATABASE_URL` in the environment before starting the service."</code> | <code>"Run the API with `uvicorn app.main:app --reload`."</code> |
| grounded | false | <code>true</code> | <code>true</code> |
| step_path | false | <code>["retrieve_docs", "generate_answer"]</code> | <code>["retrieve_docs", "generate_answer"]</code> |
| retrieved_chunk_ids | true | <code>["config.md#1", "config.md#2", "deployment.md#1"]</code> | <code>["deployment.md#1", "config.md#1", "config.md#2"]</code> |
| citation_sources | true | <code>["sample_docs/config.md", "sample_docs/config.md"]</code> | <code>["sample_docs/deployment.md", "sample_docs/config.md"]</code> |

## Latency

- Before: `2 ms`
- After: `3 ms`
- Delta: `1 ms`
