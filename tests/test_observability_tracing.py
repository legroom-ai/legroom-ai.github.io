"""Tests for Langfuse/OTEL tracing helpers."""

from __future__ import annotations

import pytest
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from legroom.observability import (
    LegroomTracer,
    LangfuseTracingConfig,
    get_langfuse_tracing_status,
    reset_legroom_tracing,
    set_legroom_tracer,
)
from legroom.transforms.pipeline import TransformPipeline


def test_langfuse_tracing_config_builds_trace_endpoint() -> None:
    config = LangfuseTracingConfig(
        enabled=True,
        public_key="pk-lf-test",
        secret_key="sk-lf-test",
        base_url="https://cloud.langfuse.com",
        service_name="legroom-proxy",
    )

    assert config.endpoint == "https://cloud.langfuse.com/api/public/otel/v1/traces"
    assert config.headers["x-langfuse-ingestion-version"] == "4"
    assert config.headers["Authorization"].startswith("Basic ")
    assert "sk-lf-test" not in repr(config)


def test_transform_pipeline_emits_trace_spans() -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "legroom-test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    set_legroom_tracer(LegroomTracer(tracer_provider=provider))

    try:
        pipeline = TransformPipeline(transforms=[])
        messages = [{"role": "user", "content": "hello world"}]
        pipeline.apply(messages, model="gpt-4o", model_limit=1024)

        spans = exporter.get_finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.name == "legroom.compression.pipeline"
        assert span.attributes["legroom.model"] == "gpt-4o"
        assert span.attributes["legroom.tokens.before"] >= 1
        assert span.attributes["legroom.tokens.after"] >= 1
    finally:
        reset_legroom_tracing()


def test_pipeline_span_emits_gen_ai_request_model() -> None:
    """The compression-pipeline span carries the v1 OTel GenAI semconv descriptor
    (gen_ai.request.model) alongside legroom.*, so it groups by the standard
    schema. operation.name / provider.name / usage.* are intentionally v2."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "legroom-test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    set_legroom_tracer(LegroomTracer(tracer_provider=provider))

    try:
        pipeline = TransformPipeline(transforms=[])
        pipeline.apply(
            [{"role": "user", "content": "hello world"}],
            model="claude-3-5-sonnet-20241022",
            model_limit=1024,
        )

        span = exporter.get_finished_spans()[0]
        assert span.name == "legroom.compression.pipeline"
        assert span.attributes["gen_ai.request.model"] == "claude-3-5-sonnet-20241022"
        # v1 deliberately emits ONLY request.model — no operation/provider/usage
        # (each is inaccurate at this span; see pipeline.py).
        assert "gen_ai.operation.name" not in span.attributes
        assert "gen_ai.provider.name" not in span.attributes
        assert "gen_ai.usage.input_tokens" not in span.attributes
    finally:
        reset_legroom_tracing()


def test_pipeline_span_omits_request_model_when_model_missing() -> None:
    """gen_ai.request.model is omitted (not set to an empty string) when no model
    is provided — never emit a blank standard attribute."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "legroom-test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    set_legroom_tracer(LegroomTracer(tracer_provider=provider))

    try:
        pipeline = TransformPipeline(transforms=[])
        pipeline.apply([{"role": "user", "content": "hi"}], model="", model_limit=1024)
        span = exporter.get_finished_spans()[0]
        assert span.name == "legroom.compression.pipeline"
        assert "gen_ai.request.model" not in span.attributes
    finally:
        reset_legroom_tracing()


def test_pipeline_runs_with_metrics_disabled() -> None:
    """record_metrics=False takes the nullcontext (no-span) path: the run still
    returns a valid result and emits no spans (guards that building span_attributes
    with the gen_ai key never breaks the non-recording path)."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "legroom-test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    set_legroom_tracer(LegroomTracer(tracer_provider=provider))

    try:
        pipeline = TransformPipeline(transforms=[])
        result = pipeline.apply(
            [{"role": "user", "content": "hi"}],
            model="gpt-4o",
            model_limit=1024,
            record_metrics=False,
        )
        assert result.messages  # pipeline produced output
        assert exporter.get_finished_spans() == ()
    finally:
        reset_legroom_tracing()


def test_langfuse_tracing_status_defaults_to_unconfigured() -> None:
    reset_legroom_tracing()
    status = get_langfuse_tracing_status()
    assert status["configured"] is False
    assert status["enabled"] is False


def test_langfuse_tracing_requires_explicit_enable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")

    config = LangfuseTracingConfig.from_env(default_service_name="legroom-proxy")

    assert config.enabled is False
