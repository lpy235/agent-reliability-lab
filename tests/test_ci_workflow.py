from __future__ import annotations

from pathlib import Path

import yaml


def test_ci_uploads_harness_artifacts():
    workflow = yaml.safe_load(Path(".github/workflows/ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["verify"]["steps"]

    baseline_steps = [step for step in steps if step.get("name") == "Compare Docs QA baseline"]
    upload_steps = [step for step in steps if step.get("uses") == "actions/upload-artifact@v4"]

    assert baseline_steps == [
        {
            "name": "Compare Docs QA baseline",
            "run": (
                "arl-baseline baselines/docs_qa_eval_report.json reports/eval-report.json "
                "\\\n  --report-path reports/baseline-comparison.md "
                "\\\n  --json-report-path reports/baseline-comparison.json\n"
            ),
        }
    ]
    assert upload_steps == [
        {
            "name": "Upload reliability artifacts",
            "if": "always()",
            "uses": "actions/upload-artifact@v4",
            "with": {
                "name": "agent-reliability-lab-reports",
                "path": "reports/*.md\nreports/*.json\nruns.db\n",
                "if-no-files-found": "warn",
                "retention-days": 14,
            },
        }
    ]
