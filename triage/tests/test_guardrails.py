import pytest

from triage_agent.guardrails import check_note

ALLOWED = {"slo-availability-burn.md", "dynamodb-errors.md"}


def test_valid_note_passes(good_note, page_alert):
    assert check_note(good_note, page_alert, ALLOWED) == []


@pytest.mark.parametrize("step, rule", [
    ("Run terraform destroy and re-apply", "terraform_destroy"),
    ("rm -rf /var/lib/app to clear the cache", "rm_rf"),
    ("aws dynamodb delete-table --table-name incidents", "delete_table"),
    ("kubectl delete pod app-1", "kubectl_delete"),
    ("docker system prune -a", "docker_prune"),
    ("git push --force origin main", "git_force_push"),
])
def test_destructive_commands_are_blocked(good_note, page_alert, step, rule):
    good_note["first_steps"] = [step]
    assert f"destructive_command:{rule}" in check_note(good_note, page_alert, ALLOWED)


def test_force_new_deployment_is_allowed(good_note, page_alert):
    good_note["first_steps"] = ["aws ecs update-service --force-new-deployment"]
    assert check_note(good_note, page_alert, ALLOWED) == []


def test_a_page_cannot_be_downgraded(good_note, page_alert):
    good_note["severity"] = "low"
    assert "severity_too_low_for_page" in check_note(good_note, page_alert, ALLOWED)


def test_note_must_cite_a_runbook_it_was_given(good_note, page_alert):
    good_note["runbook"] = "made-up-runbook.md"
    assert "runbook_not_in_context" in check_note(good_note, page_alert, ALLOWED)


def test_missing_fields_and_bad_shapes(page_alert):
    violations = check_note({"severity": "urgent", "first_steps": "do things"}, page_alert, ALLOWED)
    assert "missing_field:title" in violations
    assert "invalid_severity" in violations
    assert "first_steps_shape" in violations


def test_secret_like_values_are_blocked(good_note, page_alert):
    good_note["first_steps"] = ["export AWS key AKIAABCDEFGHIJKLMNOP"]
    assert "secret_like_value" in check_note(good_note, page_alert, ALLOWED)


def test_non_object_is_rejected(page_alert):
    assert check_note(None, page_alert, ALLOWED) == ["not_a_json_object"]
