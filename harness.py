from __future__ import annotations

import argparse
import json
from pathlib import Path

from agents.docs_qa_agent import DocsQAAgent
from agents.llm import RuleBasedLLMClient
from agents.paths import resolve_demo_path
from evals.runner import run_eval_file
from tracing.store import SQLiteTraceStore


def run_harness(
    question: str,
    docs_dir: str,
    cases_path: str,
    issue_cases_path: str,
    db_path: str,
    report_path: str,
    issue_report_path: str,
    json_report_path: str | None = None,
    issue_json_report_path: str | None = None,
) -> dict:
    store = SQLiteTraceStore(db_path)
    resolved_docs_dir = resolve_demo_path(docs_dir)
    resolved_cases_path = resolve_demo_path(cases_path)
    resolved_issue_cases_path = resolve_demo_path(issue_cases_path)
    agent = DocsQAAgent(docs_dir=resolved_docs_dir, llm_client=RuleBasedLLMClient(), store=store)
    qa_result = agent.answer(question)
    eval_summary = run_eval_file(
        cases_path=resolved_cases_path,
        docs_dir=resolved_docs_dir,
        db_path=db_path,
        report_path=report_path,
        json_report_path=json_report_path,
    )
    issue_eval_summary = run_eval_file(
        cases_path=resolved_issue_cases_path,
        docs_dir=resolved_docs_dir,
        db_path=db_path,
        report_path=issue_report_path,
        json_report_path=issue_json_report_path,
    )
    return {"sample_run": qa_result, "eval": eval_summary, "issue_triage_eval": issue_eval_summary}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Agent Reliability Lab MVP harness.")
    parser.add_argument("--question", default="How do I configure the database?")
    parser.add_argument("--docs-dir", default="sample_docs")
    parser.add_argument("--cases-path", default="evals/cases/docs_qa.jsonl")
    parser.add_argument("--issue-cases-path", default="evals/cases/issue_triage.jsonl")
    parser.add_argument("--db-path", default="runs.db")
    parser.add_argument("--report-path", default="reports/eval-report.md")
    parser.add_argument("--issue-report-path", default="reports/issue-triage-report.md")
    parser.add_argument("--json-report-path", default="reports/eval-report.json")
    parser.add_argument("--issue-json-report-path", default="reports/issue-triage-report.json")
    args = parser.parse_args()

    result = run_harness(
        question=args.question,
        docs_dir=args.docs_dir,
        cases_path=args.cases_path,
        issue_cases_path=args.issue_cases_path,
        db_path=args.db_path,
        report_path=args.report_path,
        issue_report_path=args.issue_report_path,
        json_report_path=args.json_report_path,
        issue_json_report_path=args.issue_json_report_path,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["eval"]["failed"] or result["issue_triage_eval"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
