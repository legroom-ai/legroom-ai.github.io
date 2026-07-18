"""Transform modules for Legroom SDK."""

from __future__ import annotations

import importlib.util
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Expose concrete types to static analysis while keeping runtime imports lazy.
    from legroom.transforms.anchor_selector import (  # noqa: F401
        AnchorSelector,
        AnchorStrategy,
        AnchorWeights,
        DataPattern,
        calculate_information_score,
        compute_item_hash,
    )
    from legroom.transforms.base import Transform  # noqa: F401
    from legroom.transforms.cache_aligner import CacheAligner  # noqa: F401
    from legroom.transforms.code_compressor import (  # noqa: F401
        CodeAwareCompressor,
        CodeCompressionResult,
        CodeCompressorConfig,
        CodeLanguage,
        DocstringMode,
        detect_language,
        is_tree_sitter_available,
    )
    from legroom.transforms.content_detector import (  # noqa: F401
        ContentType,
        DetectionResult,
        detect_content_type,
    )
    from legroom.transforms.content_router import (  # noqa: F401
        CompressionStrategy,
        ContentRouter,
        ContentRouterConfig,
        RouterCompressionResult,
    )
    from legroom.transforms.diff_compressor import (  # noqa: F401
        DiffCompressionResult,
        DiffCompressor,
        DiffCompressorConfig,
    )
    from legroom.transforms.html_extractor import (  # noqa: F401
        HTMLExtractionResult,
        HTMLExtractor,
        HTMLExtractorConfig,
        is_html_content,
    )
    from legroom.transforms.log_compressor import (  # noqa: F401
        LogCompressionResult,
        LogCompressor,
        LogCompressorConfig,
    )
    from legroom.transforms.pipeline import TransformPipeline  # noqa: F401
    from legroom.transforms.search_compressor import (  # noqa: F401
        SearchCompressionResult,
        SearchCompressor,
        SearchCompressorConfig,
    )
    from legroom.transforms.smart_crusher import SmartCrusher, SmartCrusherConfig  # noqa: F401
    from legroom.transforms.tabular_ingest import (  # noqa: F401
        TabularCompressionResult,
        TabularCompressor,
        TabularCompressorConfig,
    )

_HTML_EXTRACTOR_AVAILABLE = importlib.util.find_spec("trafilatura") is not None

__all__ = [
    # Base
    "Transform",
    "TransformPipeline",
    # Anchor selection
    "AnchorSelector",
    "AnchorStrategy",
    "AnchorWeights",
    "DataPattern",
    "calculate_information_score",
    "compute_item_hash",
    # JSON compression
    "SmartCrusher",
    "SmartCrusherConfig",
    # Text compression (coding tasks)
    "ContentType",
    "DetectionResult",
    "detect_content_type",
    "SearchCompressor",
    "SearchCompressorConfig",
    "SearchCompressionResult",
    "LogCompressor",
    "LogCompressorConfig",
    "LogCompressionResult",
    "TabularCompressor",
    "TabularCompressorConfig",
    "TabularCompressionResult",
    "DiffCompressor",
    "DiffCompressorConfig",
    "DiffCompressionResult",
    # Code-aware compression (AST-based)
    "CodeAwareCompressor",
    "CodeCompressorConfig",
    "CodeCompressionResult",
    "CodeLanguage",
    "DocstringMode",
    "detect_language",
    "is_tree_sitter_available",
    # Content routing
    "ContentRouter",
    "ContentRouterConfig",
    "RouterCompressionResult",
    "CompressionStrategy",
    # Other transforms
    "CacheAligner",
    # HTML extraction (optional)
    "_HTML_EXTRACTOR_AVAILABLE",
]

# Conditionally add HTML extractor exports
if _HTML_EXTRACTOR_AVAILABLE:
    __all__.extend(
        [
            "HTMLExtractor",
            "HTMLExtractorConfig",
            "HTMLExtractionResult",
            "is_html_content",
        ]
    )

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # Base
    "Transform": ("legroom.transforms.base", "Transform"),
    "TransformPipeline": ("legroom.transforms.pipeline", "TransformPipeline"),
    # Anchor selection
    "AnchorSelector": ("legroom.transforms.anchor_selector", "AnchorSelector"),
    "AnchorStrategy": ("legroom.transforms.anchor_selector", "AnchorStrategy"),
    "AnchorWeights": ("legroom.transforms.anchor_selector", "AnchorWeights"),
    "DataPattern": ("legroom.transforms.anchor_selector", "DataPattern"),
    "calculate_information_score": (
        "legroom.transforms.anchor_selector",
        "calculate_information_score",
    ),
    "compute_item_hash": ("legroom.transforms.anchor_selector", "compute_item_hash"),
    # JSON compression
    "SmartCrusher": ("legroom.transforms.smart_crusher", "SmartCrusher"),
    "SmartCrusherConfig": ("legroom.transforms.smart_crusher", "SmartCrusherConfig"),
    # Text compression (coding tasks)
    "ContentType": ("legroom.transforms.content_detector", "ContentType"),
    "DetectionResult": ("legroom.transforms.content_detector", "DetectionResult"),
    "detect_content_type": ("legroom.transforms.content_detector", "detect_content_type"),
    "SearchCompressor": ("legroom.transforms.search_compressor", "SearchCompressor"),
    "SearchCompressorConfig": (
        "legroom.transforms.search_compressor",
        "SearchCompressorConfig",
    ),
    "SearchCompressionResult": (
        "legroom.transforms.search_compressor",
        "SearchCompressionResult",
    ),
    "LogCompressor": ("legroom.transforms.log_compressor", "LogCompressor"),
    "LogCompressorConfig": ("legroom.transforms.log_compressor", "LogCompressorConfig"),
    "LogCompressionResult": ("legroom.transforms.log_compressor", "LogCompressionResult"),
    "TabularCompressor": ("legroom.transforms.tabular_ingest", "TabularCompressor"),
    "TabularCompressorConfig": (
        "legroom.transforms.tabular_ingest",
        "TabularCompressorConfig",
    ),
    "TabularCompressionResult": (
        "legroom.transforms.tabular_ingest",
        "TabularCompressionResult",
    ),
    "DiffCompressor": ("legroom.transforms.diff_compressor", "DiffCompressor"),
    "DiffCompressorConfig": ("legroom.transforms.diff_compressor", "DiffCompressorConfig"),
    "DiffCompressionResult": (
        "legroom.transforms.diff_compressor",
        "DiffCompressionResult",
    ),
    # Code-aware compression (AST-based)
    "CodeAwareCompressor": ("legroom.transforms.code_compressor", "CodeAwareCompressor"),
    "CodeCompressorConfig": ("legroom.transforms.code_compressor", "CodeCompressorConfig"),
    "CodeCompressionResult": (
        "legroom.transforms.code_compressor",
        "CodeCompressionResult",
    ),
    "CodeLanguage": ("legroom.transforms.code_compressor", "CodeLanguage"),
    "DocstringMode": ("legroom.transforms.code_compressor", "DocstringMode"),
    "detect_language": ("legroom.transforms.code_compressor", "detect_language"),
    "is_tree_sitter_available": (
        "legroom.transforms.code_compressor",
        "is_tree_sitter_available",
    ),
    # Content routing
    "ContentRouter": ("legroom.transforms.content_router", "ContentRouter"),
    "ContentRouterConfig": ("legroom.transforms.content_router", "ContentRouterConfig"),
    "RouterCompressionResult": (
        "legroom.transforms.content_router",
        "RouterCompressionResult",
    ),
    "CompressionStrategy": ("legroom.transforms.content_router", "CompressionStrategy"),
    # Other transforms
    "CacheAligner": ("legroom.transforms.cache_aligner", "CacheAligner"),
    # HTML extraction (optional dependency - requires trafilatura)
    "HTMLExtractor": ("legroom.transforms.html_extractor", "HTMLExtractor"),
    "HTMLExtractorConfig": ("legroom.transforms.html_extractor", "HTMLExtractorConfig"),
    "HTMLExtractionResult": ("legroom.transforms.html_extractor", "HTMLExtractionResult"),
    "is_html_content": ("legroom.transforms.html_extractor", "is_html_content"),
}


def __getattr__(name: str) -> object:
    if name == "__path__":
        raise AttributeError(name)
    if name == "_HTML_EXTRACTOR_AVAILABLE":
        return _HTML_EXTRACTOR_AVAILABLE

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
