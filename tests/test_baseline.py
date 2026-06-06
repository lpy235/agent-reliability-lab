from __future__ import annotations

import json
from pathlib import Path

from evals.baseline import compare_eval_reports, write_baseline_json_report, write_baseline_report
from evals.runner import run_eval_file


def _write_report(path, results):
    path.write_text(
        json.dumps(
            {
                "generated_at": "example",
                "summary": {
                    "total": len(results),
                    "passed": sum(1 for result in results if result["passed"]),
                    "failed": sum(1 for result in results if not result["passed"]),
                    "pass_rate": 0.0,
                },
                "results": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_compare_eval_reports_finds_regressions_improvements_added_and_removed(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    _write_report(
        baseline_path,
        [
            {"case_id": "case_regressed", "agent": "docs_qa", "passed": True, "run_id": "run_1", "latency_ms": 10, "checks": []},
            {
                "case_id": "case_improved",
                "agent": "docs_qa",
                "passed": False,
                "run_id": "run_2",
                "latency_ms": 11,
                "checks": [{"name": "required_keyword:DATABASE_URL", "passed": False}],
            },
            {"case_id": "case_removed", "agent": "docs_qa", "passed": True, "run_id": "run_3", "latency_ms": 12, "checks": []},
        ],
    )
    _write_report(
        candidate_path,
        [
            {
                "case_id": "case_regressed",
                "agent": "docs_qa",
                "passed": False,
                "run_id": "run_4",
                "latency_ms": 13,
                "checks": [{"name": "required_citation:sample_docs/config.md", "passed": False}],
            },
            {"case_id": "case_improved", "agent": "docs_qa", "passed": True, "run_id": "run_5", "latency_ms": 14, "checks": []},
            {"case_id": "case_added", "agent": "docs_qa", "passed": True, "run_id": "run_6", "latency_ms": 15, "checks": []},
        ],
    )

    comparison = compare_eval_reports(baseline_path, candidate_path)

    assert comparison["summary"]["regressions"] == 1
    assert comparison["summary"]["improvements"] == 1
    assert comparison["summary"]["added"] == 1
    assert comparison["summary"]["removed"] == 1
    assert comparison["regressions"][0]["case_id"] == "case_regressed"
    assert comparison["regressions"][0]["new_failed_checks"] == ["required_citation:sample_docs/config.md"]


def test_write_baseline_report(tmp_path):
    comparison = {
        "baseline_path": "baseline.json",
        "candidate_path": "candidate.json",
        "summary": {
            "baseline_total": 1,
            "candidate_total": 1,
            "shared": 1,
            "regressions": 1,
            "improvements": 0,
            "added": 0,
            "removed": 0,
        },
        "regressions": [
            {
                "case_id": "case_regressed",
                "before": {"passed": True},
                "after": {"passed": False},
                "new_failed_checks": ["required_keyword:DATABASE_URL"],
            }
        ],
        "improvements": [],
        "unchanged": [],
        "added": [],
        "removed": [],
    }
    report_path = tmp_path / "baseline-comparison.md"

    result = write_baseline_report(comparison, report_path)

    assert result["baseline_report_path"] == str(report_path)
    text = report_path.read_text(encoding="utf-8")
    assert "Regressions: `1`" in text
    assert "required_keyword:DATABASE_URL" in text


def test_write_baseline_json_report(tmp_path):
    comparison = {
        "baseline_path": "baseline.json",
        "candidate_path": "candidate.json",
        "summary": {
            "baseline_total": 1,
            "candidate_total": 1,
            "shared": 1,
            "regressions": 0,
            "improvements": 0,
            "added": 0,
            "removed": 0,
        },
        "regressions": [],
        "improvements": [],
        "unchanged": [
            {
                "case_id": "case_stable",
                "before": {"passed": True},
                "after": {"passed": True},
                "new_failed_checks": [],
            }
        ],
        "added": [],
        "removed": [],
    }
    report_path = tmp_path / "baseline-comparison.json"

    result = write_baseline_json_report(comparison, report_path)

    assert result["baseline_json_report_path"] == str(report_path)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["summary"]["regressions"] == 0
    assert payload["unchanged"][0]["case_id"] == "case_stable"


def test_docs_qa_baseline_matches_current_eval(tmp_path):
    candidate_path = tmp_path / "candidate.json"

    run_eval_file(
        cases_path="evals/cases/docs_qa.jsonl",
        docs_dir="sample_docs",
        db_path=tmp_path / "runs.db",
        report_path=tmp_path / "eval-report.md",
        json_report_path=candidate_path,
    )
    comparison = compare_eval_reports(Path("baselines/docs_qa_eval_report.json"), candidate_path)

    assert comparison["summary"]["shared"] == 2
    assert comparison["summary"]["regressions"] == 0


def test_issue_triage_baseline_matches_current_eval(tmp_path):
    candidate_path = tmp_path / "candidate.json"

    run_eval_file(
        cases_path="evals/cases/issue_triage.jsonl",
        docs_dir="sample_docs",
        db_path=tmp_path / "runs.db",
        report_path=tmp_path / "issue-triage-report.md",
        json_report_path=candidate_path,
    )
    comparison = compare_eval_reports(Path("baselines/issue_triage_eval_report.json"), candidate_path)

    assert comparison["summary"]["shared"] == 3
    assert comparison["summary"]["regressions"] == 0
