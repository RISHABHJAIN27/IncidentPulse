"""Checks every LLM triage draft must pass before anyone sees it.

A draft that fails is sent back to the model once with the reasons, then
replaced by a rule-based note built from the runbook (see graph.py).
"""

import json
import re

from .alerts import Alert

SEVERITIES = ("low", "medium", "high", "critical")
REQUIRED_FIELDS = ("severity", "title", "likely_cause", "first_steps", "runbook")

# Never let an automated triage note suggest something irreversible.
DESTRUCTIVE_PATTERNS = {
    "rm_rf": r"\brm\s+-[a-z]*r[a-z]*f|\brm\s+-[a-z]*f[a-z]*r",
    "terraform_destroy": r"terraform\s+destroy",
    "delete_table": r"delete[-_ ]table|drop\s+table|truncate\s+table",
    "delete_service": r"(ecs|aws)\s+[\w-]*\s*delete[-_](service|cluster)",
    "kubectl_delete": r"kubectl\s+delete",
    "docker_prune": r"docker\s+(system|volume)\s+prune",
    "force_flag": r"--force\b(?!-new-deployment)",
    "git_force_push": r"git\s+push\s+.*(-f\b|--force)",
}
SECRET_PATTERN = r"AKIA[0-9A-Z]{16}|aws_secret_access_key\s*[=:]"


def check_note(note: dict | None, alert: Alert, allowed_runbooks: set[str]) -> list[str]:
    """Return the guardrail violations for a draft; an empty list means it passes."""
    if not isinstance(note, dict):
        return ["not_a_json_object"]

    violations = [f"missing_field:{f}" for f in REQUIRED_FIELDS if f not in note]

    severity = note.get("severity")
    if severity not in SEVERITIES:
        violations.append("invalid_severity")
    elif alert.severity_label == "page" and severity not in ("high", "critical"):
        # The model must not downplay something that already paged a human.
        violations.append("severity_too_low_for_page")

    title = note.get("title")
    if not isinstance(title, str) or not 5 <= len(title.strip()) <= 120:
        violations.append("title_length")

    steps = note.get("first_steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 6 or not all(isinstance(s, str) and s.strip() for s in steps):
        violations.append("first_steps_shape")

    if note.get("runbook") not in allowed_runbooks:
        # Grounding check: the note must cite a runbook it was actually given.
        violations.append("runbook_not_in_context")

    text = json.dumps(note).lower()
    for name, pattern in DESTRUCTIVE_PATTERNS.items():
        if re.search(pattern, text):
            violations.append(f"destructive_command:{name}")
    if re.search(SECRET_PATTERN, json.dumps(note), re.IGNORECASE):
        violations.append("secret_like_value")

    return violations
