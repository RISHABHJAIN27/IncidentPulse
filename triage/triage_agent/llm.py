"""Model and tracing setup: Ollama for chat and embeddings, LangFuse for LLM traces."""

import logging

from .config import Settings

log = logging.getLogger(__name__)


def make_llm(settings: Settings):
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        format="json",  # constrain the model to emit a JSON object
        temperature=0,  # same alert, same triage
        num_predict=512,
        client_kwargs={"timeout": 120},
    )


def make_embeddings_factory(settings: Settings):
    def factory():
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=settings.ollama_embed_model, base_url=settings.ollama_base_url)

    return factory


def langfuse_callbacks(settings: Settings) -> list:
    """LangFuse callback handler (traces every graph run, node and LLM call), if enabled.

    Reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY and LANGFUSE_BASE_URL from the environment.
    """
    if not settings.langfuse_enabled:
        return []
    try:
        from langfuse.langchain import CallbackHandler

        return [CallbackHandler()]
    except Exception as exc:
        log.warning("LangFuse tracing disabled: %s", exc)
        return []


def flush_langfuse(settings: Settings) -> None:
    if settings.langfuse_enabled:
        try:
            from langfuse import get_client

            get_client().flush()
        except Exception:
            pass
