# Safety And Tool Policy Design

## Purpose

Safety checks add lightweight guardrails to the agent reliability workflow. The goal is not to build a full security product; it is to make safety violations observable and regression-testable.

## Scope

This phase implements:

- PII redaction for emails, phone numbers, and simple API keys.
- Tool policy checks for `dry_run`, `approval_required`, and `forbidden` tools.
- Max tool call count checks.
- Safety violations included in agent outputs and eval checks.
- Issue Triage integration because it already simulates tool calls.

## Tool Policy Defaults

```python
{
  "search_similar_issues": {"mode": "dry_run"},
  "infer_owner": {"mode": "dry_run"},
  "assign_label": {"mode": "dry_run", "approval_required": True},
  "delete_issue": {"mode": "forbidden"},
}
```

`assign_label` remains dry-run but records an approval-required violation unless explicit approval is supplied later. This makes the policy visible without mutating GitHub.

## Eval Expectations

Issue triage cases may assert:

- `max_safety_violations`
- `required_safety_checks`
- `forbidden_redacted_tokens`

## Acceptance Criteria

- PII redaction replaces emails, phone numbers, and API-key-like strings.
- Forbidden tools and approval-required tools are recorded as safety violations.
- Issue Triage output includes `redacted_input` and `safety`.
- JSONL evals can pass/fail on safety expectations.
- Existing tests continue to pass.

