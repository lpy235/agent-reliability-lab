import json

import pytest

from evals.metrics import evaluate_docs_qa
from evals.runner import run_eval_file


def test_evaluate_docs_qa_passes_expected_result():
    result = {
        "answer": "Set DATABASE_URL in the environment.",
        "citations": [{"source": "sample_docs/config.md"}],
        "grounded": True,
        "latency_ms": 10,
    }
    expected = {
        "required_citations": ["sample_docs/config.md"],
        "required_keywords": ["DATABASE_URL"],
        "forbidden_keywords": ["I don't know"],
        "max_latency_ms": 5000,
        "grounded": True,
    }

    evaluation = evaluate_docs_qa(result, expected)

    assert evaluation["passed"] is True
    assert all(check["passed"] for check in evaluation["checks"])


def test_evaluate_docs_qa_fails_missing_keyword():
    result = {
        "answer": "Use an environment variable.",
        "citations": [{"source": "sample_docs/config.md"}],
        "grounded": True,
        "latency_ms": 10,
    }
    expected = {"required_keywords": ["DATABASE_URL"]}

    evaluation = evaluate_docs_qa(result, expected)

    assert evaluation["passed"] is False
    assert evaluation["checks"][0]["name"] == "required_keyword:DATABASE_URL"


def test_run_eval_file_writes_report(tmp_path):
    cases_path = tmp_path / "cases.jsonl"
    report_path = tmp_path / "report.md"
    db_path = tmp_path / "runs.db"
    cases_path.write_text(
        json.dumps(
            {
                "case_id": "docs_qa_001",
                "agent": "docs_qa",
                "input": {"question": "How do I configure the database?"},
                "expected": {"required_keywords": ["DATABASE_URL"], "required_citations": ["sample_docs/config.md"]},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    summary = run_eval_file(cases_path=cases_path, docs_dir="sample_docs", db_path=db_path, report_path=report_path)

    assert summary["total"] == 1
    assert summary["failed"] == 0
    assert "docs_qa_001" in report_path.read_text(encoding="utf-8")


def test_run_eval_file_supports_issue_triage(tmp_path):
    cases_path = tmp_path / "issue_cases.jsonl"
    report_path = tmp_path / "issue-report.md"
    db_path = tmp_path / "runs.db"
    cases_path.write_text(
        json.dumps(
            {
                "case_id": "issue_bug_001",
                "agent": "issue_triage",
                "input": {
                    "title": "App crashes when uploading large files",
                    "body": "The upload page freezes after selecting a 2GB file.",
                },
                "expected": {
                    "label": "bug",
                    "priority": "high",
                    "required_tool_calls": ["search_similar_issues", "assign_label"],
                    "required_safety_checks": ["approval_required"],
                    "max_safety_violations": 1,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    summary = run_eval_file(cases_path=cases_path, docs_dir="sample_docs", db_path=db_path, report_path=report_path)

    assert summary["total"] == 1
    assert summary["failed"] == 0
    assert "issue_bug_001" in report_path.read_text(encoding="utf-8")


def test_invalid_jsonl_reports_line_number(tmp_path):
    cases_path = tmp_path / "bad.jsonl"
    cases_path.write_text("{bad json}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="bad.jsonl:1"):
        run_eval_file(cases_path=cases_path, docs_dir="sample_docs", db_path=tmp_path / "runs.db", report_path=tmp_path / "report.md")
