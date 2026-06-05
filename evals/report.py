from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    failed = sum(1 for result in results if not result["passed"])
    passed = total - failed
    pass_rate = 0.0 if total == 0 else passed / total
    return {"total": total, "passed": passed, "failed": failed, "pass_rate": pass_rate}


def write_markdown_report(results: list[dict[str, Any]], report_path: str | Path) -> dict[str, Any]:
    summary = summarize_results(results)
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Agent Reliability Lab Eval Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Total: {summary['total']}",
        f"Passed: {summary['passed']}",
        f"Failed: {summary['failed']}",
        f"Pass rate: {summary['pass_rate']:.1%}",
        "",
        "| Case | Status | Run ID | Latency |",
        "| --- | --- | --- | ---: |",
    ]
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(f"| {result['case_id']} | {status} | {result['run_id']} | {result['latency_ms']} ms |")

    failures = [result for result in results if not result["passed"]]
    if failures:
        lines.extend(["", "## Failures", ""])
        for result in failures:
            lines.append(f"### {result['case_id']}")
            for check in result["checks"]:
                if not check["passed"]:
                    lines.append(f"- {check['name']}: expected `{check['expected']}`, got `{check['actual']}`")
            lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {**summary, "report_path": str(path)}


def write_json_report(results: list[dict[str, Any]], report_path: str | Path) -> dict[str, Any]:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summarize_results(results),
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"json_report_path": str(path)}
