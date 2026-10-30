"""Opens and resolves incidents on the Incident Pulse status page.

The status page shares a database with the API it reports on, so the moment
we most need to post an incident (DynamoDB down) is when posting fails.
Failed publishes are kept and retried; see docs/failure-mode-analysis.md, row 6.
"""

import logging
import threading

import httpx

log = logging.getLogger(__name__)


class IncidentPublisher:
    def __init__(self, base_url: str, client: httpx.Client | None = None):
        self.client = client or httpx.Client(base_url=base_url, timeout=10)
        self._incidents: dict[str, str] = {}  # alert key -> incident id
        self._pending_open: dict[str, dict] = {}  # alert key -> note
        self._pending_resolve: set[str] = set()
        self._lock = threading.Lock()

    def known(self, alert_key: str) -> bool:
        with self._lock:
            return alert_key in self._incidents or alert_key in self._pending_open

    def open(self, alert_key: str, note: dict) -> str | None:
        try:
            resp = self.client.post("/incidents", json={"title": note["title"], "severity": note["severity"]})
            resp.raise_for_status()
            incident_id = resp.json()["id"]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            log.warning("could not open incident, will retry: %s", exc)
            with self._lock:
                self._pending_open[alert_key] = note
            return None
        with self._lock:
            self._incidents[alert_key] = incident_id
            self._pending_open.pop(alert_key, None)
        return incident_id

    def resolve(self, alert_key: str) -> bool:
        with self._lock:
            if self._pending_open.pop(alert_key, None) is not None:
                return True  # never got published; nothing to resolve
            incident_id = self._incidents.get(alert_key)
        if incident_id is None:
            return False
        try:
            resp = self.client.patch(f"/incidents/{incident_id}", json={"status": "resolved"})
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.warning("could not resolve incident %s, will retry: %s", incident_id, exc)
            with self._lock:
                self._pending_resolve.add(alert_key)
            return False
        with self._lock:
            self._incidents.pop(alert_key, None)
            self._pending_resolve.discard(alert_key)
        return True

    def retry_pending(self) -> None:
        with self._lock:
            opens = dict(self._pending_open)
            resolves = set(self._pending_resolve)
        for key, note in opens.items():
            self.open(key, note)
        for key in resolves:
            self.resolve(key)

    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending_open) + len(self._pending_resolve)
