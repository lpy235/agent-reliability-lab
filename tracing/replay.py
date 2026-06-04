from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agents.docs_qa_agent import DocsQAAgent
from agents.llm import RuleBasedLLMClient
from agents.paths import resolve_demo_path
from tracing.store import SQLiteTraceStore


def extract_retrieved_chunks(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for step in steps:
        if step["name"] != "retrieve_docs":
            continue
        for event in step.get("events", []):
            if event.get("type") in {"retrieval", "replay_retrieval"}:
                return list(event.get("chunks", []))
    return []


def replay_run(
    run_id: str,
    db_path: str | Path = "runs.db",
    fixed_context: bool = True,
    docs_dir: str | None = None,
) -> dict[str, Any]:
    store = SQLiteTraceStore(db_path)
    store.init_schema()
    source_run = store.get_run(run_id)
    question = source_run["input"]["question"]
    replay_docs_dir = resolve_demo_path(docs_dir or source_run["input"].get("docs_dir", "sample_docs"))
    source_steps = store.list_steps(run_id)
    chunks = extract_retrieved_chunks(source_steps) if fixed_context else None

    if fixed_context and not chunks:
        raise ValueError(f"Run {run_id} has no retrieved chunks to replay")

    agent = DocsQAAgent(docs_dir=replay_docs_dir, llm_client=RuleBasedLLMClient(), store=store)
    result = agent.answer(question, retrieved_chunks=chunks, source_run_id=run_id)
    return {
        "source_run_id": run_id,
        "replay_run_id": result["run_id"],
        "fixed_context": fixed_context,
        "result": result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay a saved Agent Reliability Lab run.")
    parser.add_argument("run_id")
    parser.add_argument("--db-path", default="runs.db")
    parser.add_argument("--docs-dir")
    parser.add_argument("--live-context", action="store_true", help="Rerun retrieval instead of reusing saved chunks.")
    args = parser.parse_args()

    replay = replay_run(
        run_id=args.run_id,
        db_path=args.db_path,
        fixed_context=not args.live_context,
        docs_dir=args.docs_dir,
    )
    print(json.dumps(replay, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
