from triage_agent.alerts import Alert
from triage_agent.knowledge import RunbookRetriever, retrieve_for_alert, section_items


def test_runbooks_are_split_by_section(chunks):
    sources = {c.source for c in chunks}
    assert {"dynamodb-errors.md", "replica-down.md", "slo-availability-burn.md"} <= sources
    assert any(c.section == "First steps" for c in chunks)


def test_section_items_reads_numbered_steps(chunks):
    steps = section_items(chunks, "dynamodb-errors.md", "First steps")
    assert len(steps) >= 3
    assert "/ready" in steps[0]


def test_keyword_search_finds_the_dynamodb_runbook(retriever):
    results = retriever.search("ReadTimeoutError talking to DynamoDB table", k=3)
    assert results[0].source == "dynamodb-errors.md"


def test_camel_case_alert_names_match_runbook_words(retriever):
    results = retriever.search("IncidentPulseLatencyBudgetBurnFast", k=2)
    assert results[0].source == "slo-latency-burn.md"


def test_runbook_named_by_the_alert_is_always_first(retriever, page_alert):
    context = retrieve_for_alert(retriever, page_alert)
    assert context[0].source == "slo-availability-burn.md"
    assert all(c.source == "slo-availability-burn.md" for c in context[:5])


def test_falls_back_to_keyword_search_when_embeddings_fail(chunks):
    def broken_embeddings():
        raise ConnectionError("ollama is down")

    retriever = RunbookRetriever(chunks, broken_embeddings)
    alert = Alert(labels={"alertname": "IncidentPulseReplicaDown", "severity": "ticket"})
    results = retrieve_for_alert(retriever, alert)
    assert retriever.last_mode == "keyword"
    assert results[0].source == "replica-down.md"


def test_vector_search_works_with_an_embedding_model(chunks):
    # Uses a deterministic fake embedding model, so this exercises the real vector
    # store code path (similarity search needs numpy) without Ollama running.
    from langchain_core.embeddings import DeterministicFakeEmbedding

    retriever = RunbookRetriever(chunks, lambda: DeterministicFakeEmbedding(size=64))
    results = retriever.search("DynamoDB timeouts", k=3)

    assert retriever.last_mode == "vector"
    assert len(results) == 3
    assert {c.source for c in results} <= {c.source for c in chunks}
