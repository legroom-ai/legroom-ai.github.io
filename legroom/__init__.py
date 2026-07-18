"""
Legroom - The Context Optimization Layer for LLM Applications.

Cut your LLM costs by 50-90% without losing accuracy.

Legroom wraps LLM clients to provide:
- Smart compression of tool outputs (keeps errors, anomalies, relevant items)
- Cache-aligned prefix optimization for better provider cache hits
- Rolling window token management for long conversations
- Full streaming support with zero accuracy loss

Quick Start:

    from legroom import LegroomClient, OpenAIProvider
    from openai import OpenAI

    # Wrap your existing client
    client = LegroomClient(
        original_client=OpenAI(),
        provider=OpenAIProvider(),
        default_mode="optimize",
    )

    # Use exactly like the original client
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Hello!"},
        ],
    )

    # Check savings
    stats = client.get_stats()
    print(f"Tokens saved: {stats['session']['tokens_saved_total']}")

Verify It's Working:

    # Validate configuration
    result = client.validate_setup()
    if not result["valid"]:
        print("Issues:", result)

    # Enable logging to see what's happening
    import logging
    logging.basicConfig(level=logging.INFO)
    # INFO:legroom.transforms.pipeline:Pipeline complete: 45000 -> 4500 tokens

Simulate Before Sending:

    plan = client.chat.completions.simulate(
        model="gpt-4o",
        messages=large_messages,
    )
    print(f"Would save {plan.tokens_saved} tokens")
    print(f"Transforms: {plan.transforms}")

Error Handling:

    from legroom import LegroomError, ConfigurationError, ProviderError

    try:
        response = client.chat.completions.create(...)
    except ConfigurationError as e:
        print(f"Config issue: {e.details}")
    except LegroomError as e:
        print(f"Legroom error: {e}")

For more examples, see https://github.com/legroom-sdk/legroom/tree/main/examples
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from ._ort import ensure_ort_dylib_pinned
from ._version import __version__  # noqa: F401

# Must run before anything can import `legroom._core`: on Windows the
# Rust core resolves onnxruntime.dll at runtime (ort load-dynamic), and
# the bare DLL search lands on the Windows ML System32 build, which
# deadlocks ort session init (Win11 24H2+). Windows-gated, idempotent,
# ~microseconds. See `legroom/_ort.py` for the full story.
ensure_ort_dylib_pinned()

from .compress import CompressConfig, CompressResult, compress, compress_spreadsheet  # noqa: E402

# Keep a real callable bound for the one-function compression API so
# `from legroom import compress` is never shadowed by the submodule object.

__all__ = [
    # Main client
    "LegroomClient",
    # Providers
    "Provider",
    "TokenCounter",
    "OpenAIProvider",
    "AnthropicProvider",
    # Exceptions
    "LegroomError",
    "ConfigurationError",
    "ProviderError",
    "StorageError",
    "CompressionError",
    "TokenizationError",
    "CacheError",
    "ValidationError",
    "TransformError",
    # Config
    "LegroomConfig",
    "LegroomMode",
    "SmartCrusherConfig",
    "CacheAlignerConfig",
    "CacheOptimizerConfig",
    "RelevanceScorerConfig",
    # Data models
    "Block",
    "CachePrefixMetrics",
    "DiffArtifact",
    "RequestMetrics",
    "SimulationResult",
    "TransformDiff",
    "TransformResult",
    "WasteSignals",
    # Transforms
    "SmartCrusher",
    "CacheAligner",
    "TransformPipeline",
    # Cache optimizers
    "BaseCacheOptimizer",
    "CacheConfig",
    "CacheMetrics",
    "CacheResult",
    "CacheStrategy",
    "OptimizationContext",
    "CacheOptimizerRegistry",
    "AnthropicCacheOptimizer",
    "OpenAICacheOptimizer",
    "GoogleCacheOptimizer",
    "SemanticCache",
    "SemanticCacheLayer",
    # Relevance scoring - BM25 always available, embeddings require sentence-transformers
    "RelevanceScore",
    "RelevanceScorer",
    "BM25Scorer",
    "EmbeddingScorer",
    "HybridScorer",
    "create_scorer",
    "embedding_available",
    # Utilities
    "Tokenizer",
    "count_tokens_text",
    "count_tokens_messages",
    "generate_report",
    # Observability
    "LegroomOtelMetrics",
    "LegroomTracer",
    "LangfuseTracingConfig",
    "OTelMetricsConfig",
    "configure_otel_metrics",
    "configure_langfuse_tracing",
    "get_legroom_tracer",
    "get_langfuse_tracing_status",
    "get_otel_metrics",
    "get_otel_metrics_status",
    "reset_legroom_tracing",
    "reset_otel_metrics",
    # Memory - optional hierarchical memory system
    "with_memory",  # Main user-facing API
    "Memory",
    "ScopeLevel",
    "HierarchicalMemory",
    "MemoryConfig",
    "EmbedderBackend",
    # One-function compression API
    "compress",
    "compress_spreadsheet",
    "CompressConfig",
    "CompressResult",
    # Hooks
    "CompressionHooks",
    "CompressContext",
    "CompressEvent",
    # Canonical pipeline
    "PipelineStage",
    "PipelineEvent",
    "PipelineExtensionManager",
    "CANONICAL_PIPELINE_STAGES",
    # Shared context for multi-agent workflows
    "SharedContext",
]

# Keep package-level imports lightweight so `import legroom` does not eagerly
# load provider SDKs, ML stacks, or optional proxy/runtime integrations.
_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # Main client
    "LegroomClient": ("legroom.client", "LegroomClient"),
    # Providers
    "Provider": ("legroom.providers", "Provider"),
    "TokenCounter": ("legroom.providers", "TokenCounter"),
    "OpenAIProvider": ("legroom.providers", "OpenAIProvider"),
    "AnthropicProvider": ("legroom.providers", "AnthropicProvider"),
    # Exceptions
    "LegroomError": ("legroom.exceptions", "LegroomError"),
    "ConfigurationError": ("legroom.exceptions", "ConfigurationError"),
    "ProviderError": ("legroom.exceptions", "ProviderError"),
    "StorageError": ("legroom.exceptions", "StorageError"),
    "CompressionError": ("legroom.exceptions", "CompressionError"),
    "TokenizationError": ("legroom.exceptions", "TokenizationError"),
    "CacheError": ("legroom.exceptions", "CacheError"),
    "ValidationError": ("legroom.exceptions", "ValidationError"),
    "TransformError": ("legroom.exceptions", "TransformError"),
    # Config
    "LegroomConfig": ("legroom.config", "LegroomConfig"),
    "LegroomMode": ("legroom.config", "LegroomMode"),
    "SmartCrusherConfig": ("legroom.config", "SmartCrusherConfig"),
    "CacheAlignerConfig": ("legroom.config", "CacheAlignerConfig"),
    "CacheOptimizerConfig": ("legroom.config", "CacheOptimizerConfig"),
    "RelevanceScorerConfig": ("legroom.config", "RelevanceScorerConfig"),
    # Data models
    "Block": ("legroom.config", "Block"),
    "CachePrefixMetrics": ("legroom.config", "CachePrefixMetrics"),
    "DiffArtifact": ("legroom.config", "DiffArtifact"),
    "RequestMetrics": ("legroom.config", "RequestMetrics"),
    "SimulationResult": ("legroom.config", "SimulationResult"),
    "TransformDiff": ("legroom.config", "TransformDiff"),
    "TransformResult": ("legroom.config", "TransformResult"),
    "WasteSignals": ("legroom.config", "WasteSignals"),
    # Transforms
    "SmartCrusher": ("legroom.transforms", "SmartCrusher"),
    "CacheAligner": ("legroom.transforms", "CacheAligner"),
    "TransformPipeline": ("legroom.transforms", "TransformPipeline"),
    # Cache optimizers
    "BaseCacheOptimizer": ("legroom.cache", "BaseCacheOptimizer"),
    "CacheConfig": ("legroom.cache", "CacheConfig"),
    "CacheMetrics": ("legroom.cache", "CacheMetrics"),
    "CacheResult": ("legroom.cache", "CacheResult"),
    "CacheStrategy": ("legroom.cache", "CacheStrategy"),
    "OptimizationContext": ("legroom.cache", "OptimizationContext"),
    "CacheOptimizerRegistry": ("legroom.cache", "CacheOptimizerRegistry"),
    "AnthropicCacheOptimizer": ("legroom.cache", "AnthropicCacheOptimizer"),
    "OpenAICacheOptimizer": ("legroom.cache", "OpenAICacheOptimizer"),
    "GoogleCacheOptimizer": ("legroom.cache", "GoogleCacheOptimizer"),
    "SemanticCache": ("legroom.cache", "SemanticCache"),
    "SemanticCacheLayer": ("legroom.cache", "SemanticCacheLayer"),
    # Relevance scoring
    "RelevanceScore": ("legroom.relevance", "RelevanceScore"),
    "RelevanceScorer": ("legroom.relevance", "RelevanceScorer"),
    "BM25Scorer": ("legroom.relevance", "BM25Scorer"),
    "EmbeddingScorer": ("legroom.relevance", "EmbeddingScorer"),
    "HybridScorer": ("legroom.relevance", "HybridScorer"),
    "create_scorer": ("legroom.relevance", "create_scorer"),
    "embedding_available": ("legroom.relevance", "embedding_available"),
    # Utilities
    "Tokenizer": ("legroom.tokenizer", "Tokenizer"),
    "count_tokens_text": ("legroom.tokenizer", "count_tokens_text"),
    "count_tokens_messages": ("legroom.tokenizer", "count_tokens_messages"),
    "generate_report": ("legroom.reporting", "generate_report"),
    # Observability
    "LegroomOtelMetrics": ("legroom.observability", "LegroomOtelMetrics"),
    "LegroomTracer": ("legroom.observability", "LegroomTracer"),
    "LangfuseTracingConfig": ("legroom.observability", "LangfuseTracingConfig"),
    "OTelMetricsConfig": ("legroom.observability", "OTelMetricsConfig"),
    "configure_otel_metrics": ("legroom.observability", "configure_otel_metrics"),
    "configure_langfuse_tracing": ("legroom.observability", "configure_langfuse_tracing"),
    "get_legroom_tracer": ("legroom.observability", "get_legroom_tracer"),
    "get_langfuse_tracing_status": ("legroom.observability", "get_langfuse_tracing_status"),
    "get_otel_metrics": ("legroom.observability", "get_otel_metrics"),
    "get_otel_metrics_status": ("legroom.observability", "get_otel_metrics_status"),
    "reset_legroom_tracing": ("legroom.observability", "reset_legroom_tracing"),
    "reset_otel_metrics": ("legroom.observability", "reset_otel_metrics"),
    # One-function API
    "compress": ("legroom.compress", "compress"),
    "compress_spreadsheet": ("legroom.compress", "compress_spreadsheet"),
    # Hooks
    "CompressionHooks": ("legroom.hooks", "CompressionHooks"),
    "CompressContext": ("legroom.hooks", "CompressContext"),
    "CompressEvent": ("legroom.hooks", "CompressEvent"),
    # Canonical pipeline
    "PipelineStage": ("legroom.pipeline", "PipelineStage"),
    "PipelineEvent": ("legroom.pipeline", "PipelineEvent"),
    "PipelineExtensionManager": ("legroom.pipeline", "PipelineExtensionManager"),
    "CANONICAL_PIPELINE_STAGES": ("legroom.pipeline", "CANONICAL_PIPELINE_STAGES"),
    # Shared context
    "SharedContext": ("legroom.shared_context", "SharedContext"),
}

# Memory remains optional and preserves the long-standing behavior of exposing
# `None` when the extra dependencies are not installed.
_OPTIONAL_EXPORTS = {
    "with_memory": ("legroom.memory", "with_memory"),
    "Memory": ("legroom.memory", "Memory"),
    "ScopeLevel": ("legroom.memory", "ScopeLevel"),
    "HierarchicalMemory": ("legroom.memory", "HierarchicalMemory"),
    "MemoryConfig": ("legroom.memory", "MemoryConfig"),
    "EmbedderBackend": ("legroom.memory", "EmbedderBackend"),
}


def __getattr__(name: str) -> Any:
    """Resolve package exports lazily while preserving legacy import paths."""
    module_attr = _LAZY_EXPORTS.get(name)
    if module_attr is not None:
        module_name, attr_name = module_attr
        value = getattr(import_module(module_name), attr_name)
        globals()[name] = value
        return value

    optional_module_attr = _OPTIONAL_EXPORTS.get(name)
    if optional_module_attr is not None:
        module_name, attr_name = optional_module_attr
        try:
            value = getattr(import_module(module_name), attr_name)
        except ImportError:
            value = None
        globals()[name] = value
        return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
