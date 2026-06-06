from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_eval_report(report_path: str | Path) -> dict[str, Any]:
    path = Path(report_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "results" not in payload or not isinstance(payload["results"], list):
        raise ValueError(f"Invalid eval report: {path}")
    return payload


def compare_eval_reports(baseline_path: str | Path, candidate_path: str | Path) -> dict[str, Any]:
    baseline = load_eval_report(baseline_path)
    candidate = load_eval_report(candidate_path)
    baseline_cases = {result["case_id"]: result for result in baseline["results"]}
    candidate_cases = {result["case_id"]: result for result in candidate["results"]}

    shared_case_ids = sorted(set(baseline_cases) & set(candidate_cases))
    regressions = []
    improvements = []
    unchanged = []
    for case_id in shared_case_ids:
        before = baseline_cases[case_id]
        after = candidate_cases[case_id]
        comparison = _compare_case(case_id, before, after)
        if before["passed"] and not after["passed"]:
            regressions.append(comparison)
        elif not before["passed"] and after["passed"]:
            improvements.append(comparison)
        else:
            unchanged.append(comparison)

    added = [_case_summary(candidate_cases[case_id]) for case_id in sorted(set(candidate_cases) - set(baseline_cases))]
    removed = [_case_summary(baseline_cases[case_id]) for case_id in sorted(set(baseline_cases) - set(candidate_cases))]

    return {
        "baseline_path": str(baseline_path),
        "candidate_path": str(candidate_path),
        "summary": {
            "baseline_total": len(baseline_cases),
            "candidate_total": len(candidate_cases),
            "shared": len(shared_case_ids),
            "regressions": len(regressions),
            "improvements": len(improvements),
            "added": len(added),
            "removed": len(removed),
        },
        "regressions": regressions,
        "improvements": improvements,
        "unchanged": unchanged,
        "added": added,
        "removed": removed,
    }


def write_baseline_report(comparison: dict[str, Any], report_path: str | Path) -> dict[str, str]:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = comparison["summary"]
    lines = [
        "# Agent Reliability Lab Baseline Comparison",
        "",
        f"Baseline: `{comparison['baseline_path']}`",
        f"Candidate: `{comparison['candidate_path']}`",
        "",
        "## Summary",
        "",
        f"- Baseline cases: `{summary['baseline_total']}`",
        f"- Candidate cases: `{summary['candidate_total']}`",
        f"- Shared cases: `{summary['shared']}`",
        f"- Regressions: `{summary['regressions']}`",
        f"- Improvements: `{summary['improvements']}`",
        f"- Added: `{summary['added']}`",
        f"- Removed: `{summary['removed']}`",
    ]
    lines.extend(_section("Regressions", comparison["regressions"]))
    lines.extend(_section("Improvements", comparison["improvements"]))
    lines.extend(_section("Added Cases", comparison["added"]))
    lines.extend(_section("Removed Cases", comparison["removed"]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"baseline_report_path": str(path)}


def write_baseline_json_report(comparison: dict[str, Any], report_path: str | Path) -> dict[str, str]:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(comparison, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"baseline_json_report_path": str(path)}


def _compare_case(case_id: str, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "before": _case_summary(before),
        "after": _case_summary(after),
        "new_failed_checks": _failed_check_names(after),
    }


def _case_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": result["case_id"],
        "agent": result.get("agent"),
        "passed": result["passed"],
        "run_id": result.get("run_id"),
        "latency_ms": result.get("latency_ms"),
        "failed_checks": _failed_check_names(result),
    }


def _failed_check_names(result: dict[str, Any]) -> list[str]:
    return [check["name"] for check in result.get("checks", []) if not check.get("passed")]


def _section(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = ["", f"## {title}", ""]
    if not items:
        lines.append("None.")
        return lines

    lines.extend(["| Case | Before | After | Failed checks |", "| --- | --- | --- | --- |"])
    for item in items:
        if "before" in item and "after" in item:
            before = "PASS" if item["before"]["passed"] else "FAIL"
            after = "PASS" if item["after"]["passed"] else "FAIL"
            failed_checks = ", ".join(item.get("new_failed_checks", [])) or "-"
            lines.append(f"| {item['case_id']} | {before} | {after} | {failed_checks} |")
        else:
            status = "PASS" if item["passed"] else "FAIL"
            failed_checks = ", ".join(item.get("failed_checks", [])) or "-"
            lines.append(f"| {item['case_id']} | - | {status} | {failed_checks} |")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two Agent Reliability Lab JSON eval reports.")
    parser.add_argument("baseline_report")
    parser.add_argument("candidate_report")
    parser.add_argument("--report-path", default="reports/baseline-comparison.md")
    parser.add_argument("--json-report-path")
    args = parser.parse_args()

    comparison = compare_eval_reports(args.baseline_report, args.candidate_report)
    report = write_baseline_report(comparison, args.report_path)
    json_report = write_baseline_json_report(comparison, args.json_report_path) if args.json_report_path else {}
    summary = comparison["summary"]
    json_report_suffix = (
        f", JSON: {json_report['baseline_json_report_path']}" if json_report else ""
    )
    print(
        "Baseline comparison complete: "
        f"{summary['regressions']} regressions, "
        f"{summary['improvements']} improvements. "
        f"Report: {report['baseline_report_path']}"
        f"{json_report_suffix}"
    )
    return 1 if summary["regressions"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
