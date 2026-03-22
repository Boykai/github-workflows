"""OpenTelemetry setup — conditional initialisation gated by ``OTEL_ENABLED``.

This module is only imported when ``settings.otel_enabled`` is ``True``.
When OTel is disabled, the ``get_tracer()`` and ``get_meter()`` helpers
return no-op instances so instrumented code can call them unconditionally.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.logging_utils import get_logger

if TYPE_CHECKING:
    from opentelemetry.metrics import Meter
    from opentelemetry.trace import Tracer

logger = get_logger(__name__)

_tracer: Tracer | None = None
_meter: Meter | None = None


class _RequestIDSpanProcessor:
    """SpanProcessor that injects the current X-Request-ID into every span."""

    def on_start(self, span, parent_context=None) -> None:  # type: ignore[no-untyped-def]
        from src.middleware.request_id import request_id_var

        rid = request_id_var.get("")
        if rid:
            span.set_attribute("request.id", rid)

    def on_end(self, span) -> None:  # type: ignore[no-untyped-def]
        pass

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


def init_otel(service_name: str, endpoint: str) -> tuple[Tracer, Meter]:
    """Initialise OTel TracerProvider, MeterProvider, and auto-instrumentors.

    Returns the active ``(Tracer, Meter)`` tuple.
    """
    global _tracer, _meter

    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": service_name})

    # ── Tracing ──
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    tracer_provider.add_span_processor(_RequestIDSpanProcessor())  # type: ignore[arg-type]
    trace.set_tracer_provider(tracer_provider)

    # ── Metrics ──
    metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # ── Auto-instrumentation ──
    FastAPIInstrumentor.instrument()  # type: ignore[call-arg]  # OTel classmethod
    HTTPXClientInstrumentor().instrument()
    SQLite3Instrumentor().instrument()

    _tracer = trace.get_tracer(service_name)
    _meter = metrics.get_meter(service_name)

    logger.info(
        "OpenTelemetry initialised: service=%s endpoint=%s",
        service_name,
        endpoint,
    )
    return _tracer, _meter


class _NoOpSpan:
    """Minimal no-op span that satisfies the context-manager protocol."""

    def set_attribute(self, key: str, value: object) -> None:
        pass

    def __enter__(self):  # type: ignore[no-untyped-def]
        return self

    def __exit__(self, *args: object) -> None:
        pass


class _NoOpTracer:
    """Lightweight no-op tracer — avoids importing ``opentelemetry``."""

    def start_as_current_span(self, name: str, **kwargs: object):  # type: ignore[no-untyped-def]
        return _NoOpSpan()


class _NoOpMeter:
    """Lightweight no-op meter — avoids importing ``opentelemetry``."""

    class _NoOpInstrument:
        def set(self, value: object, attributes: object = None) -> None:
            pass

        def record(self, value: object, attributes: object = None) -> None:
            pass

    def create_gauge(self, name: str, **kwargs: object) -> _NoOpInstrument:
        return self._NoOpInstrument()

    def create_histogram(self, name: str, **kwargs: object) -> _NoOpInstrument:
        return self._NoOpInstrument()

    def create_counter(self, name: str, **kwargs: object) -> _NoOpInstrument:
        return self._NoOpInstrument()


def get_tracer() -> Tracer:
    """Return the active tracer, or a local no-op tracer (zero OTel imports)."""
    if _tracer is not None:
        return _tracer
    return _NoOpTracer()  # type: ignore[return-value]


def get_meter() -> Meter:
    """Return the active meter, or a local no-op meter (zero OTel imports)."""
    if _meter is not None:
        return _meter
    return _NoOpMeter()  # type: ignore[return-value]
