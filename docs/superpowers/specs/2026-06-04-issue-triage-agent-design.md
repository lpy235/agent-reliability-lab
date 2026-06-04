# Issue Triage Agent Design

## Purpose

Issue Triage Agent adds a second demo agent focused on tool-use reliability rather than RAG. It classifies GitHub-style issues, records simulated tool calls, and can be evaluated through the existing JSONL regression harness.

## Scope

This phase implements:

- Deterministic issue classification.
- Priority inference.
- Dry-run next action.
- Simulated tool calls recorded in trace steps.
- JSONL eval cases and metrics.
- CLI/API/harness integration.
- Static example artifact.

This phase does not call the real GitHub API and does not assign labels or owners remotely.

## Inputs And Outputs

Input:

```json
{
  "title": "App crashes when uploading large files",
  "body": "The upload page freezes after selecting a 2GB file.",
  "repo": {"name": "demo/app", "default_branch": "main"}
}
```

Output:

```json
{
  "label": "bug",
  "priority": "high",
  "next_action": "dry_run_assign_label:bug",
  "tool_calls": [
    {"name": "search_similar_issues", "mode": "dry_run"},
    {"name": "infer_owner", "mode": "dry_run"},
    {"name": "assign_label", "mode": "dry_run"}
  ]
}
```

## Classification Rules

- `bug`: crash, error, exception, fail, freeze, broken, regression.
- `feature`: add, support, feature, request, enhancement.
- `docs`: docs, documentation, readme, typo, example.
- `question`: how, why, question, clarify, help.

Priority:

- `high`: crash, data loss, security, production, unavailable, regression.
- `medium`: bug/feature with clear user impact.
- `low`: docs/question or vague request.

## Trace Shape

Steps:

1. `analyze_issue`
2. `search_similar_issues`
3. `infer_owner`
4. `assign_label`

The last three steps are simulated dry-run tool calls, recorded as trace events with `type="tool_call"`.

## Acceptance Criteria

- Issue Triage Agent returns deterministic label, priority, next action, and tool calls.
- Trace store records the analyze and simulated tool-call steps.
- JSONL eval runner supports both `docs_qa` and `issue_triage`.
- Tests cover passing and failing issue triage eval expectations.
- API exposes `POST /agents/issue-triage/run`.

