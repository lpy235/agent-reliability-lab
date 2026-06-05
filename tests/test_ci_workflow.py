from __future__ import annotations

from pathlib import Path

import yaml


def test_ci_uploads_harness_artifacts():
    workflow = yaml.safe_load(Path(".github/workflows/ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["verify"]["steps"]

    upload_steps = [step for step in steps if step.get("uses") == "actions/upload-artifact@v4"]

    assert upload_steps == [
        {
            "name": "Upload reliability artifacts",
            "if": "always()",
            "uses": "actions/upload-artifact@v4",
            "with": {
                "name": "agent-reliability-lab-reports",
                "path": "reports/*.md\nruns.db\n",
                "if-no-files-found": "warn",
                "retention-days": 14,
            },
        }
    ]
