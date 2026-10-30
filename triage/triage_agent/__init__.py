"""AI incident triage agent for Incident Pulse.

Alertmanager -> /alerts webhook -> LangGraph agent:
    retrieve runbooks (RAG) -> draft triage note (Ollama) -> guardrails
        -> accept | retry with feedback | rule-based fallback -> publish incident
"""
