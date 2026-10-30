"""Promptfoo provider: runs the real triage agent (Ollama, guardrails, fallback) as a dry run.

Promptfoo calls call_api() once per test case; the alert comes from the test's vars.
Needs Ollama running locally and the triage requirements installed:
    pip install -r triage/requirements.txt
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "triage"))

from triage_agent.alerts import Alert  # noqa: E402
from triage_agent.config import load_settings  # noqa: E402
from triage_agent.graph import build_graph  # noqa: E402
from triage_agent.knowledge import RunbookRetriever, load_runbooks  # noqa: E402
from triage_agent.llm import langfuse_callbacks, make_embeddings_factory, make_llm  # noqa: E402

_settings = load_settings()
_retriever = RunbookRetriever(load_runbooks(_settings.runbook_dir), make_embeddings_factory(_settings))
_agent = build_graph(make_llm(_settings), _retriever, publisher=None, max_attempts=_settings.max_attempts)


def call_api(prompt, options, context):
    alert = Alert(**context["vars"]["alert"])
    state = _agent.invoke(
        {"alert": alert, "publish": False},
        config={"callbacks": langfuse_callbacks(_settings), "run_name": f"eval {alert.name}"},
    )
    result = {
        "note": state["note"],
        "fallback_used": state["fallback_used"],
        "attempts": state["attempts"],
        "rejected_drafts": [v for v in state.get("violation_log", []) if v],
        "retrieval": _retriever.last_mode,
    }
    return {"output": json.dumps(result)}
