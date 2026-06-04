from __future__ import annotations

from typing import Any


def _check(name: str, passed: bool, actual: Any, expected: Any) -> dict[str, Any]:
    return {"name": name, "passed": passed, "actual": actual, "expected": expected}


def evaluate_docs_qa(result: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    answer = result.get("answer", "")
    citation_sources = [citation.get("source") for citation in result.get("citations", [])]

    for source in expected.get("required_citations", []):
        checks.append(_check(f"required_citation:{source}", source in citation_sources, citation_sources, source))

    for keyword in expected.get("required_keywords", []):
        checks.append(_check(f"required_keyword:{keyword}", keyword.lower() in answer.lower(), answer, keyword))

    for keyword in expected.get("forbidden_keywords", []):
        checks.append(_check(f"forbidden_keyword:{keyword}", keyword.lower() not in answer.lower(), answer, keyword))

    if "max_latency_ms" in expected:
        latency = result.get("latency_ms", 0)
        checks.append(_check("max_latency_ms", latency <= expected["max_latency_ms"], latency, expected["max_latency_ms"]))

    if "grounded" in expected:
        checks.append(_check("grounded", result.get("grounded") is expected["grounded"], result.get("grounded"), expected["grounded"]))

    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def evaluate_issue_triage(result: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    tool_names = [tool.get("name") for tool in result.get("tool_calls", [])]

    if "label" in expected:
        checks.append(_check("label", result.get("label") == expected["label"], result.get("label"), expected["label"]))

    if "priority" in expected:
        checks.append(
            _check("priority", result.get("priority") == expected["priority"], result.get("priority"), expected["priority"])
        )

    for tool_name in expected.get("required_tool_calls", []):
        checks.append(_check(f"required_tool_call:{tool_name}", tool_name in tool_names, tool_names, tool_name))

    for tool_name in expected.get("forbidden_tool_calls", []):
        checks.append(_check(f"forbidden_tool_call:{tool_name}", tool_name not in tool_names, tool_names, tool_name))

    if "max_latency_ms" in expected:
        latency = result.get("latency_ms", 0)
        checks.append(_check("max_latency_ms", latency <= expected["max_latency_ms"], latency, expected["max_latency_ms"]))

    return {"passed": all(check["passed"] for check in checks), "checks": checks}
