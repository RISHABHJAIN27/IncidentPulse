import os
from dataclasses import dataclass
from pathlib import Path

_REPO_RUNBOOKS = Path(__file__).resolve().parents[2] / "runbooks"


@dataclass(frozen=True)
class Settings:
    incidentpulse_url: str
    ollama_base_url: str
    ollama_model: str
    ollama_embed_model: str
    runbook_dir: Path
    langfuse_enabled: bool
    max_attempts: int


def load_settings() -> Settings:
    return Settings(
        incidentpulse_url=os.getenv("INCIDENTPULSE_URL", "http://localhost:8080"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        ollama_embed_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        runbook_dir=Path(os.getenv("RUNBOOK_DIR", str(_REPO_RUNBOOKS))),
        langfuse_enabled=os.getenv("LANGFUSE_ENABLED", "false").lower() == "true",
        # One LLM draft plus one retry with the guardrail feedback, then fall back.
        max_attempts=int(os.getenv("TRIAGE_MAX_ATTEMPTS", "2")),
    )
