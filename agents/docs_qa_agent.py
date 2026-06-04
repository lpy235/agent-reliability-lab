from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from agents.llm import RuleBasedLLMClient
from agents.retrieval import retrieve_chunks
from tracing.sdk import Trace
from tracing.store import SQLiteTraceStore


class DocsQAAgent:
    def __init__(self, docs_dir: str | Path, llm_client=None, store: SQLiteTraceStore | None = None):
        self.docs_dir = str(docs_dir)
        self.llm_client = llm_client or RuleBasedLLMClient()
        self.store = store or SQLiteTraceStore("runs.db")

    def answer(self, question: str) -> dict[str, Any]:
        started = time.perf_counter()
        trace = Trace.start(store=self.store, agent_name="docs_qa", input={"question": question, "docs_dir": self.docs_dir})
        try:
            with trace.step("retrieve_docs") as step:
                step.log_state(before={"question": question})
                chunks = retrieve_chunks(question, docs_dir=self.docs_dir, top_k=3)
                step.log_event({"type": "retrieval", "chunks": chunks})
                step.log_decision({"next_action": "generate_answer", "reason_tags": ["chunks_found"]})
                step.log_state(after={"chunk_count": len(chunks)})

            prompt = self._build_prompt(question, chunks)
            with trace.step("generate_answer") as step:
                step.log_state(before={"question": question, "chunk_ids": [chunk["chunk_id"] for chunk in chunks]})
                response = self.llm_client.complete(prompt)
                citations = [{"source": chunk["source"], "chunk_id": chunk["chunk_id"]} for chunk in chunks[:2]]
                grounded = all(citation["chunk_id"] in {chunk["chunk_id"] for chunk in chunks} for citation in citations)
                step.record.tokens = response.tokens
                step.record.cost = response.cost
                step.log_event({"type": "llm_completion", "answer": response.text})
                step.log_decision({"next_action": "finish", "reason_tags": ["answer_generated"]})
                step.log_state(after={"answer_length": len(response.text), "citation_count": len(citations)})

            latency_ms = int((time.perf_counter() - started) * 1000)
            result = {
                "question": question,
                "answer": response.text,
                "citations": citations,
                "retrieved_chunks": chunks,
                "grounded": grounded,
                "latency_ms": latency_ms,
                "run_id": trace.run_id,
            }
            trace.finish(output=result, status="success", metrics={"latency_ms": latency_ms, "tokens": response.tokens})
            return result
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            trace.finish(output=None, status="error", metrics={"latency_ms": latency_ms}, error=str(exc))
            raise

    def _build_prompt(self, question: str, chunks: list[dict[str, Any]]) -> str:
        context = "\n\n".join(f"[{chunk['chunk_id']}] {chunk['text']}" for chunk in chunks)
        return (
            "Answer the question using only the local documentation context.\n"
            "Include facts only when they are supported by the context.\n\n"
            f"Question: {question}\n\n"
            f"Context:\n{context}"
        )
