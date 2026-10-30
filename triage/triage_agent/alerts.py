"""Alertmanager webhook payload (version 4) and the alert fields the agent uses."""

import hashlib
import json
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field


class Alert(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str = "firing"
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    startsAt: str | None = None
    fingerprint: str | None = None

    @property
    def name(self) -> str:
        return self.labels.get("alertname", "UnknownAlert")

    @property
    def severity_label(self) -> str:
        return self.labels.get("severity", "")

    @property
    def key(self) -> str:
        # Alertmanager's fingerprint identifies one alert across firing/resolved
        # notifications; fall back to a hash of the labels.
        if self.fingerprint:
            return self.fingerprint
        raw = json.dumps(self.labels, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()[:16]

    def runbook_file(self) -> str | None:
        url = self.annotations.get("runbook_url", "")
        name = PurePosixPath(url).name
        return name if name.endswith(".md") else None

    def as_text(self) -> str:
        """The alert as plain text, for retrieval and for the prompt."""
        lines = [f"alertname: {self.name}", f"status: {self.status}"]
        for key in ("summary", "description"):
            if key in self.annotations:
                lines.append(f"{key}: {self.annotations[key]}")
        other = {k: v for k, v in self.labels.items() if k != "alertname"}
        if other:
            lines.append("labels: " + ", ".join(f"{k}={v}" for k, v in sorted(other.items())))
        return "\n".join(lines)


class AlertmanagerWebhook(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: str = "4"
    status: str = "firing"
    alerts: list[Alert] = Field(default_factory=list)
