"""Runbook knowledge base for retrieval-augmented triage.

Runbooks (runbooks/*.md) are split into one chunk per "## " section. Retrieval:
  1. Context engineering: if the alert names a runbook (annotation runbook_url),
     that whole runbook is always in context, first.
  2. Semantic search over every chunk with Ollama embeddings adds related
     sections from other runbooks.
  3. If Ollama is unreachable, a keyword retriever takes over, so triage still
     works (with a weaker match) during an LLM outage.
"""

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .alerts import Alert

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Chunk:
    source: str  # runbook file name, e.g. dynamodb-errors.md
    section: str  # section heading, e.g. First steps
    text: str

    def render(self) -> str:
        return f"[{self.source} / {self.section}]\n{self.text}"


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_runbooks(runbook_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(Path(runbook_dir).glob("*.md")):
        content = path.read_text(encoding="utf-8")
        title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
        alerts_match = re.search(r"^Alerts?: (.+)$", content, re.MULTILINE)
        header = "\n".join(m.group(0) for m in (title_match, alerts_match) if m)
        for section in re.split(r"^## ", content, flags=re.MULTILINE)[1:]:
            heading, _, body = section.partition("\n")
            chunks.append(Chunk(path.name, heading.strip(), f"{header}\n## {heading.strip()}\n{body.strip()}"))
    if not chunks:
        raise FileNotFoundError(f"no runbooks found in {runbook_dir}")
    return chunks


def section_items(chunks: list[Chunk], source: str, heading: str) -> list[str]:
    """List items (numbered or bulleted) from one section of one runbook."""
    for chunk in chunks:
        if chunk.source == source and chunk.section.lower() == heading.lower():
            items = re.findall(r"^\s*(?:\d+\.|-)\s+(.+)$", chunk.text, re.MULTILINE)
            return [item.strip() for item in items]
    return []


# ---------------------------------------------------------------------------
# Retrievers
# ---------------------------------------------------------------------------

_WORD = re.compile(r"[a-z0-9]+")


def _stem(token: str) -> str:
    # Light plural stemming so "timeouts" matches "timeout" and "errors" matches "error".
    return token[:-1] if len(token) > 4 and token.endswith("s") and not token.endswith("ss") else token


def _tokens(text: str) -> list[str]:
    # Split CamelCase alert names so IncidentPulseLatencyBudgetBurnFast matches "latency".
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return [_stem(t) for t in _WORD.findall(text.lower()) if len(t) > 2]


class KeywordRetriever:
    """TF-IDF style scoring. No model needed: the fallback when Ollama is down."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.doc_tokens = [Counter(_tokens(c.text)) for c in chunks]
        df = Counter(t for tokens in self.doc_tokens for t in tokens)
        n = len(chunks)
        self.idf = {t: math.log((n + 1) / (count + 0.5)) for t, count in df.items()}

    def search(self, query: str, k: int = 4) -> list[Chunk]:
        q = set(_tokens(query))
        scored = []
        for chunk, tokens in zip(self.chunks, self.doc_tokens):
            score = sum(self.idf.get(t, 0.0) * (1 + math.log(tokens[t])) for t in q if t in tokens)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [chunk for _, chunk in scored[:k]]


class VectorRetriever:
    """Semantic search with Ollama embeddings in an in-memory vector store."""

    def __init__(self, chunks: list[Chunk], embeddings):
        from langchain_core.documents import Document
        from langchain_core.vectorstores import InMemoryVectorStore

        self.store = InMemoryVectorStore(embedding=embeddings)
        self.store.add_documents([
            Document(page_content=c.text, metadata={"source": c.source, "section": c.section}) for c in chunks
        ])
        self._by_key = {(c.source, c.section): c for c in chunks}

    def search(self, query: str, k: int = 4) -> list[Chunk]:
        docs = self.store.similarity_search(query, k=k)
        return [self._by_key[(d.metadata["source"], d.metadata["section"])] for d in docs]


class RunbookRetriever:
    """Vector search when Ollama is reachable, keyword search otherwise.

    The vector index is built lazily and rebuilt on the next request if Ollama
    was down, so the agent recovers without a restart.
    """

    def __init__(self, chunks: list[Chunk], embeddings_factory=None):
        self.chunks = chunks
        self.keyword = KeywordRetriever(chunks)
        self._embeddings_factory = embeddings_factory
        self._vector: VectorRetriever | None = None
        self.last_mode = "keyword"

    def search(self, query: str, k: int = 4) -> list[Chunk]:
        if self._embeddings_factory is not None:
            try:
                if self._vector is None:
                    self._vector = VectorRetriever(self.chunks, self._embeddings_factory())
                results = self._vector.search(query, k)
                self.last_mode = "vector"
                return results
            except Exception as exc:  # Ollama down or model missing
                log.warning("vector retrieval unavailable, using keyword search: %s", exc)
                self._vector = None
        self.last_mode = "keyword"
        return self.keyword.search(query, k)


def retrieve_for_alert(retriever: RunbookRetriever, alert: Alert, k: int = 4, limit: int = 8) -> list[Chunk]:
    context: list[Chunk] = []
    named = alert.runbook_file()
    if named:
        context.extend(c for c in retriever.chunks if c.source == named)
    for chunk in retriever.search(alert.as_text(), k):
        if chunk not in context:
            context.append(chunk)
    return context[:limit]
