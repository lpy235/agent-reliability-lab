from safety.pii_redactor import redact_issue_input, redact_pii
from safety.tool_policy import ToolPolicy


def test_redact_pii_replaces_email_phone_and_api_key():
    text = "Email dev@example.com or call +1 555-123-4567 with sk_test_123456789abc."

    redacted, findings = redact_pii(text)

    assert "dev@example.com" not in redacted
    assert "+1 555-123-4567" not in redacted
    assert "sk_test_123456789abc" not in redacted
    assert {"type": "email", "value": "dev@example.com"} in findings
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_API_KEY]" in redacted


def test_redact_issue_input_combines_findings():
    redacted, findings = redact_issue_input("Contact dev@example.com", "Phone 555-123-4567")

    assert redacted["title"] == "Contact [REDACTED_EMAIL]"
    assert "[REDACTED_PHONE]" in redacted["body"]
    assert [item["type"] for item in findings] == ["email", "phone"]


def test_tool_policy_marks_approval_and_forbidden_tools():
    policy = ToolPolicy(max_tool_calls=1)

    assign = policy.check_tool("assign_label")
    delete = policy.check_tool("delete_issue")
    max_violations = policy.check_max_tool_calls([{"name": "a"}, {"name": "b"}])

    assert assign.allowed is True
    assert assign.violation == "approval_required"
    assert delete.allowed is False
    assert delete.violation == "forbidden_tool"
    assert max_violations[0]["type"] == "max_tool_calls"
