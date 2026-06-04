from harness import run_harness


def test_harness_runs_sample_question_and_eval(tmp_path):
    result = run_harness(
        question="How do I configure the database?",
        docs_dir="sample_docs",
        cases_path="evals/cases/docs_qa.jsonl",
        issue_cases_path="evals/cases/issue_triage.jsonl",
        db_path=str(tmp_path / "runs.db"),
        report_path=str(tmp_path / "eval-report.md"),
        issue_report_path=str(tmp_path / "issue-report.md"),
    )

    assert "DATABASE_URL" in result["sample_run"]["answer"]
    assert result["eval"]["total"] == 2
    assert result["eval"]["failed"] == 0
    assert result["issue_triage_eval"]["total"] == 3
    assert result["issue_triage_eval"]["failed"] == 0
