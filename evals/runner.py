from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agents.docs_qa_agent import DocsQAAgent
from agents.issue_triage_agent import IssueTriageAgent
from agents.llm import RuleBasedLLMClient
from agents.paths import resolve_demo_path
from evals.metrics import evaluate_docs_qa, evaluate_issue_triage
from evals.report import write_markdown_report
from tracing.store import SQLiteTraceStore


def load_cases(cases_path: str | Path) -> list[dict[str, Any]]:
    path = resolve_demo_path(cases_path)
    cases = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path.name}:{line_no}: {exc.msg}") from exc
    return cases


def run_eval_file(cases_path: str | Path, docs_dir: str | Path, db_path: str | Path, report_path: str | Path) -> dict[str, Any]:
    store = SQLiteTraceStore(db_path)
    resolved_docs_dir = resolve_demo_path(docs_dir)
    docs_agent = DocsQAAgent(docs_dir=resolved_docs_dir, llm_client=RuleBasedLLMClient(), store=store)
    issue_agent = IssueTriageAgent(store=store)
    results = []

    for case in load_cases(cases_path):
        agent_name = case.get("agent")
        if agent_name == "docs_qa":
            output = docs_agent.answer(case["input"]["question"])
            evaluation = evaluate_docs_qa(output, case.get("expected", {}))
        elif agent_name == "issue_triage":
            output = issue_agent.triage(
                title=case["input"]["title"],
                body=case["input"].get("body", ""),
                repo=case["input"].get("repo", {}),
            )
            evaluation = evaluate_issue_triage(output, case.get("expected", {}))
        else:
            raise ValueError(f"Unsupported agent: {agent_name}")
        results.append(
            {
                "case_id": case["case_id"],
                "agent": agent_name,
                "run_id": output["run_id"],
                "passed": evaluation["passed"],
                "checks": evaluation["checks"],
                "latency_ms": output["latency_ms"],
                "output": output,
            }
        )

    return write_markdown_report(results, report_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Agent Reliability Lab JSONL evals.")
    parser.add_argument("cases_path")
    parser.add_argument("--docs-dir", default="sample_docs")
    parser.add_argument("--db-path", default="runs.db")
    parser.add_argument("--report-path", default="reports/eval-report.md")
    args = parser.parse_args()

    summary = run_eval_file(args.cases_path, args.docs_dir, args.db_path, args.report_path)
    print(f"Eval complete: {summary['passed']}/{summary['total']} passed. Report: {summary['report_path']}")
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
