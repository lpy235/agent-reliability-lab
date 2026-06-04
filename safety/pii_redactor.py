from __future__ import annotations

import re


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
API_KEY_RE = re.compile(r"\b(?:sk|ghp|gho|github_pat)_[A-Za-z0-9_]{12,}\b")


def redact_pii(text: str) -> tuple[str, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []

    def replace(kind: str, token: str):
        def _inner(match: re.Match[str]) -> str:
            findings.append({"type": kind, "value": match.group(0)})
            return token

        return _inner

    redacted = EMAIL_RE.sub(replace("email", "[REDACTED_EMAIL]"), text)
    redacted = API_KEY_RE.sub(replace("api_key", "[REDACTED_API_KEY]"), redacted)
    redacted = PHONE_RE.sub(replace("phone", "[REDACTED_PHONE]"), redacted)
    return redacted, findings


def redact_issue_input(title: str, body: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    redacted_title, title_findings = redact_pii(title)
    redacted_body, body_findings = redact_pii(body)
    return {"title": redacted_title, "body": redacted_body}, title_findings + body_findings

