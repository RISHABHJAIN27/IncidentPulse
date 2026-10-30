"""Metrics and tracing for Incident Pulse.

Metrics
    Every request is counted and timed with Prometheus metrics. These two series are
    the raw material for the service's SLIs (see slo/ and docs/slo.md):
      - http_requests_total{method, route, status_code}
      - http_request_duration_seconds{method, route}
    They are exposed at GET /metrics for Prometheus to scrape.

Tracing
    When OTEL_ENABLED=true, OpenTelemetry creates a span for every request and a child
    span for every DynamoDB call, and exports them over OTLP to the collector
    (OTEL_EXPORTER_OTLP_ENDPOINT). It is off by default, so unit tests and the existing
    AWS deployment behave exactly as before.
"""

import os
import time

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import ENVIRONMENT


# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------

REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests handled, by route template and status code.",
    ["method", "route", "status_code"],
)

LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds, by route template.",
    ["method", "route"],
    # 0.3s is the latency SLO threshold, so it must be an exact bucket boundary.
    buckets=(0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5, 5.0),
)

# Scraping and probing endpoints are not user traffic, so they stay out of the SLIs.
UNTRACKED_PATHS = {"/metrics"}


def _route_template(request: Request) -> str:
    # Use the route template (/incidents/{incident_id}), never the raw path,
    # so one incident ID does not become one time series.
    route = request.scope.get("route")
    return getattr(route, "path", "unmatched")


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in UNTRACKED_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500  # if the handler raises, the client sees a 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            route = _route_template(request)
            REQUESTS.labels(request.method, route, str(status_code)).inc()
            LATENCY.labels(request.method, route).observe(time.perf_counter() - start)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# OpenTelemetry tracing
# ---------------------------------------------------------------------------

def setup_tracing(app) -> bool:
    """Instrument FastAPI and boto3 (DynamoDB) with OpenTelemetry, if enabled."""
    if os.getenv("OTEL_ENABLED", "false").lower() != "true":
        return False

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({
        "service.name": os.getenv("OTEL_SERVICE_NAME", "incident-pulse"),
        "service.instance.id": os.getenv("HOSTNAME", "local"),
        "deployment.environment": ENVIRONMENT,
    })
    provider = TracerProvider(resource=resource)
    # Endpoint and TLS settings come from the standard OTEL_EXPORTER_OTLP_* env vars.
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    BotocoreInstrumentor().instrument()
    FastAPIInstrumentor.instrument_app(app, excluded_urls="metrics,health")
    return True
