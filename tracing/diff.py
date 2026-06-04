from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from tracing.store import SQLiteTraceStore


def _output(run: dict[str, Any]) -> dict[str, Any]:
    return run.get("output") or {}


def _chunk_ids(run: dict[str, Any]) -> list[str]:
    return [chunk.get("chunk_id", "") for chunk in _output(run).get("retrieved_chunks", [])]


def _citation_sources(run: dict[str, Any]) -> list[str]:
    return [citation.get("source", "") for citation in _output(run).get("citations", [])]


def _latency(run: dict[str, Any]) -> int | None:
    metrics = run.get("metrics") or {}
    output = _output(run)
    return metrics.get("latency_ms", output.get("latency_ms"))


def _changed(name: str, before: Any, after: Any) -> dict[str, Any]:
    return {"field": name, "changed": before != after, "before": before, "after": after}


def diff_runs(base_run_id: str, candidate_run_id: str, db_path: str | Path = "runs.db") -> dict[str, Any]:
    store = SQLiteTraceStore(db_path)
    store.init_schema()
    base_run = store.get_run(base_run_id)
    candidate_run = store.get_run(candidate_run_id)
    base_steps = store.list_steps(base_run_id)
    candidate_steps = store.list_steps(candidate_run_id)

    base_latency = _latency(base_run)
    candidate_latency = _latency(candidate_run)
    latency_delta = None
    if base_latency is not None and candidate_latency is not None:
        latency_delta = candidate_latency - base_latency

    comparisons = [
        _changed("answer", _output(base_run).get("answer"), _output(candidate_run).get("answer")),
        _changed("grounded", _output(base_run).get("grounded"), _output(candidate_run).get("grounded")),
        _changed("step_path", [step["name"] for step in base_steps], [step["name"] for step in candidate_steps]),
        _changed("retrieved_chunk_ids", _chunk_ids(base_run), _chunk_ids(candidate_run)),
        _changed("citation_sources", _citation_sources(base_run), _citation_sources(candidate_run)),
    ]

    return {
        "base_run_id": base_run_id,
        "candidate_run_id": candidate_run_id,
        "changed": any(item["changed"] for item in comparisons),
        "comparisons": comparisons,
        "latency": {"before_ms": base_latency, "after_ms": candidate_latency, "delta_ms": latency_delta},
    }


def write_diff_report(diff: dict[str, Any], report_path: str | Path) -> dict[str, Any]:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Agent Reliability Lab Run Diff",
        "",
        f"Base run: `{diff['base_run_id']}`",
        f"Candidate run: `{diff['candidate_run_id']}`",
        f"Changed: `{diff['changed']}`",
        "",
        "## Field Changes",
        "",
        "| Field | Changed | Before | After |",
        "| --- | --- | --- | --- |",
    ]
    for item in diff["comparisons"]:
        before = _format_table_value(item["before"])
        after = _format_table_value(item["after"])
        lines.append(f"| {item['field']} | {item['changed']} | {before} | {after} |")

    latency = diff["latency"]
    lines.extend(
        [
            "",
            "## Latency",
            "",
            f"- Before: `{latency['before_ms']} ms`",
            f"- After: `{latency['after_ms']} ms`",
            f"- Delta: `{latency['delta_ms']} ms`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"report_path": str(path)}


def _format_table_value(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False)
    return f"<code>{html.escape(text)}</code>"


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff two saved Agent Reliability Lab runs.")
    parser.add_argument("base_run_id")
    parser.add_argument("candidate_run_id")
    parser.add_argument("--db-path", default="runs.db")
    parser.add_argument("--report-path")
    args = parser.parse_args()

    diff = diff_runs(args.base_run_id, args.candidate_run_id, db_path=args.db_path)
    if args.report_path:
        diff["report"] = write_diff_report(diff, args.report_path)
    print(json.dumps(diff, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
