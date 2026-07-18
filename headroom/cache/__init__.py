"""Legroom Cache Optimization Module.

This module provides a plugin-based architecture for cache optimization
across different LLM providers. Each provider has different caching
mechanisms and this module abstracts those differences.

Provider Caching Differences:
- Anthropic: Explicit cache_control blocks, 90% savings, 5-min TTL
- OpenAI: Automatic prefix caching, 50% savings, no user control
- Google: Separate CachedContent API, 75% savings + storage costs

Usage:
    from legroom.cache import CacheOptimizerRegistry, SemanticCacheLayer

    # Get provider-specific optimizer
    optimizer = CacheOptimizerRegistry.get("anthropic")
    result = optimizer.optimize(messages, context)

    # With semantic caching layer
    semantic = SemanticCacheLayer(optimizer, similarity_threshold=0.95)
    result = semantic.process(messages, context)

    # Register custom optimizer
    CacheOptimizerRegistry.register("my-provider", MyOptimizer)
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Expose concrete types to static analysis while keeping runtime imports lazy.
    from legroom.cache.anthropic import AnthropicCacheOptimizer  # noqa: F401
    from legroom.cache.base import (  # noqa: F401
        BaseCacheOptimizer,
        CacheBreakpoint,
        CacheConfig,
        CacheMetrics,
        CacheOptimizer,
        CacheResult,
        CacheStrategy,
        OptimizationContext,
    )
    from legroom.cache.compression_cache import CompressionCache  # noqa: F401
    from legroom.cache.dynamic_detector import (  # noqa: F401
        DetectorConfig,
        DynamicCategory,
        DynamicContentDetector,
        DynamicSpan,
        detect_dynamic_content,
    )
    from legroom.cache.google import GoogleCacheOptimizer  # noqa: F401
    from legroom.cache.openai import OpenAICacheOptimizer  # noqa: F401
    from legroom.cache.prefix_tracker import (  # noqa: F401
        FreezeStats,
        PrefixCacheTracker,
        PrefixFreezeConfig,
        SessionTrackerStore,
    )
    from legroom.cache.registry import CacheOptimizerRegistry  # noqa: F401
    from legroom.cache.semantic import SemanticCache, SemanticCacheLayer  # noqa: F401

__all__ = [
    # Base types
    "BaseCacheOptimizer",
    "CacheBreakpoint",
    "CacheConfig",
    "CacheMetrics",
    "CacheOptimizer",
    "CacheResult",
    "CacheStrategy",
    "OptimizationContext",
    # Dynamic content detection
    "DetectorConfig",
    "DynamicCategory",
    "DynamicContentDetector",
    "DynamicSpan",
    "detect_dynamic_content",
    # Registry
    "CacheOptimizerRegistry",
    # Provider implementations
    "AnthropicCacheOptimizer",
    "OpenAICacheOptimizer",
    "GoogleCacheOptimizer",
    # Semantic caching
    "SemanticCacheLayer",
    "SemanticCache",
    # Compression cache (token legroom mode)
    "CompressionCache",
    # Prefix cache tracking
    "PrefixCacheTracker",
    "PrefixFreezeConfig",
    "FreezeStats",
    "SessionTrackerStore",
]

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # Base types
    "BaseCacheOptimizer": ("legroom.cache.base", "BaseCacheOptimizer"),
    "CacheBreakpoint": ("legroom.cache.base", "CacheBreakpoint"),
    "CacheConfig": ("legroom.cache.base", "CacheConfig"),
    "CacheMetrics": ("legroom.cache.base", "CacheMetrics"),
    "CacheOptimizer": ("legroom.cache.base", "CacheOptimizer"),
    "CacheResult": ("legroom.cache.base", "CacheResult"),
    "CacheStrategy": ("legroom.cache.base", "CacheStrategy"),
    "OptimizationContext": ("legroom.cache.base", "OptimizationContext"),
    # Dynamic content detection
    "DetectorConfig": ("legroom.cache.dynamic_detector", "DetectorConfig"),
    "DynamicCategory": ("legroom.cache.dynamic_detector", "DynamicCategory"),
    "DynamicContentDetector": ("legroom.cache.dynamic_detector", "DynamicContentDetector"),
    "DynamicSpan": ("legroom.cache.dynamic_detector", "DynamicSpan"),
    "detect_dynamic_content": ("legroom.cache.dynamic_detector", "detect_dynamic_content"),
    # Registry
    "CacheOptimizerRegistry": ("legroom.cache.registry", "CacheOptimizerRegistry"),
    # Provider implementations
    "AnthropicCacheOptimizer": ("legroom.cache.anthropic", "AnthropicCacheOptimizer"),
    "OpenAICacheOptimizer": ("legroom.cache.openai", "OpenAICacheOptimizer"),
    "GoogleCacheOptimizer": ("legroom.cache.google", "GoogleCacheOptimizer"),
    # Semantic caching
    "SemanticCacheLayer": ("legroom.cache.semantic", "SemanticCacheLayer"),
    "SemanticCache": ("legroom.cache.semantic", "SemanticCache"),
    # Compression cache
    "CompressionCache": ("legroom.cache.compression_cache", "CompressionCache"),
    # Prefix cache tracking
    "PrefixCacheTracker": ("legroom.cache.prefix_tracker", "PrefixCacheTracker"),
    "PrefixFreezeConfig": ("legroom.cache.prefix_tracker", "PrefixFreezeConfig"),
    "FreezeStats": ("legroom.cache.prefix_tracker", "FreezeStats"),
    "SessionTrackerStore": ("legroom.cache.prefix_tracker", "SessionTrackerStore"),
}


def __getattr__(name: str) -> object:
    if name == "__path__":
        raise AttributeError(name)

    try:
        module_name, attr_name = _LAZY_EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
