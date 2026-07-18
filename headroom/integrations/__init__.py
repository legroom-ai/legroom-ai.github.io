"""Legroom integrations with popular LLM frameworks.

Available integrations:

LangChain (pip install legroom[langchain]):
    - LegroomChatModel: Drop-in wrapper for any LangChain chat model
    - LegroomChatMessageHistory: Automatic conversation compression
    - LegroomDocumentCompressor: Relevance-based document filtering
    - LegroomToolWrapper: Tool output compression for agents
    - StreamingMetricsTracker: Token counting during streaming
    - LegroomLangSmithCallbackHandler: LangSmith trace enrichment

Agno (pip install agno):
    - LegroomAgnoModel: Drop-in wrapper for any Agno model
    - LegroomPreHook/LegroomPostHook: Agent-level hooks for tracking
    - create_legroom_hooks: Convenience function to create hook pairs

CrewAI (pip install legroom[crewai]):
    - LegroomToolWrapper: Tool output compression for CrewAI agents
    - wrap_tools_with_legroom: Batch wrapper for CrewAI tools

AutoGen (pip install legroom[autogen]):
    - LegroomToolWrapper: Tool output compression for AutoGen agents
    - wrap_tools_with_legroom: Batch wrapper for AutoGen tools

MCP (Model Context Protocol):
    - LegroomMCPCompressor: Compress MCP tool results
    - compress_tool_result: Simple function for tool compression

Example:
    # LangChain integration
    from legroom.integrations import LegroomChatModel
    # or explicitly:
    from legroom.integrations.langchain import LegroomChatModel

    # Agno integration
    from legroom.integrations.agno import LegroomAgnoModel
    # or explicitly:
    from legroom.integrations.agno import LegroomAgnoModel

    # MCP integration
    from legroom.integrations import compress_tool_result
    # or explicitly:
    from legroom.integrations.mcp import compress_tool_result
"""

# Re-export from langchain subpackage for backwards compatibility
from .langchain import (
    # Retrievers
    CompressionMetrics,
    # Core
    LegroomCallbackHandler,
    # Memory
    LegroomChatMessageHistory,
    LegroomChatModel,
    LegroomDocumentCompressor,
    # LangSmith
    LegroomLangSmithCallbackHandler,
    LegroomRunnable,
    # Agents
    LegroomToolWrapper,
    OptimizationMetrics,
    # Streaming
    StreamingMetrics,
    StreamingMetricsCallback,
    StreamingMetricsTracker,
    ToolCompressionMetrics,
    ToolMetricsCollector,
    # Provider Detection
    detect_provider,
    get_legroom_provider,
    get_model_name_from_langchain,
    get_tool_metrics,
    is_langsmith_available,
    is_langsmith_tracing_enabled,
    langchain_available,
    optimize_messages,
    reset_tool_metrics,
    track_async_streaming_response,
    track_streaming_response,
    wrap_tools_with_legroom,
)

# Re-export from mcp subpackage for backwards compatibility
from .mcp import (
    DEFAULT_MCP_PROFILES,
    LegroomMCPClientWrapper,
    LegroomMCPCompressor,
    MCPCompressionResult,
    MCPToolProfile,
    compress_tool_result,
    compress_tool_result_with_metrics,
    create_legroom_mcp_proxy,
)

# Re-export from agno subpackage (optional dependency)
try:
    from .agno import (
        LegroomAgnoModel,
        LegroomPostHook,
        LegroomPreHook,
        agno_available,
        create_legroom_hooks,
        get_model_name_from_agno,
    )
    from .agno import OptimizationMetrics as AgnoOptimizationMetrics
    from .agno import get_legroom_provider as get_agno_provider
    from .agno import optimize_messages as optimize_agno_messages

    _AGNO_AVAILABLE = True
except ImportError:
    _AGNO_AVAILABLE = False

# Re-export from crewai subpackage (optional dependency)
try:
    from .crewai import (
        LegroomToolWrapper as CrewAIToolWrapper,
    )
    from .crewai import (
        ToolCompressionMetrics as CrewAIToolCompressionMetrics,
    )
    from .crewai import (
        ToolMetricsCollector as CrewAIToolMetricsCollector,
    )
    from .crewai import (
        get_tool_metrics as get_crewai_tool_metrics,
    )
    from .crewai import (
        reset_tool_metrics as reset_crewai_tool_metrics,
    )
    from .crewai import (
        wrap_tools_with_legroom as wrap_crewai_tools,
    )

    _CREWAI_AVAILABLE = True
except ImportError:
    _CREWAI_AVAILABLE = False

# Re-export from autogen subpackage (optional dependency)
try:
    from .autogen import (
        LegroomToolWrapper as AutoGenToolWrapper,
    )
    from .autogen import (
        ToolCompressionMetrics as AutoGenToolCompressionMetrics,
    )
    from .autogen import (
        ToolMetricsCollector as AutoGenToolMetricsCollector,
    )
    from .autogen import (
        get_tool_metrics as get_autogen_tool_metrics,
    )
    from .autogen import (
        reset_tool_metrics as reset_autogen_tool_metrics,
    )
    from .autogen import (
        wrap_tools_with_legroom as wrap_autogen_tools,
    )

    _AUTOGEN_AVAILABLE = True
except ImportError:
    _AUTOGEN_AVAILABLE = False

__all__ = [
    # LangChain Core
    "LegroomChatModel",
    "LegroomCallbackHandler",
    "LegroomRunnable",
    "OptimizationMetrics",
    "optimize_messages",
    "langchain_available",
    # Provider Detection
    "detect_provider",
    "get_legroom_provider",
    "get_model_name_from_langchain",
    # Memory
    "LegroomChatMessageHistory",
    # Retrievers
    "LegroomDocumentCompressor",
    "CompressionMetrics",
    # Agents
    "LegroomToolWrapper",
    "ToolCompressionMetrics",
    "ToolMetricsCollector",
    "wrap_tools_with_legroom",
    "get_tool_metrics",
    "reset_tool_metrics",
    # LangSmith
    "LegroomLangSmithCallbackHandler",
    "is_langsmith_available",
    "is_langsmith_tracing_enabled",
    # Streaming
    "StreamingMetricsTracker",
    "StreamingMetricsCallback",
    "StreamingMetrics",
    "track_streaming_response",
    "track_async_streaming_response",
    # MCP
    "LegroomMCPCompressor",
    "LegroomMCPClientWrapper",
    "MCPCompressionResult",
    "MCPToolProfile",
    "compress_tool_result",
    "compress_tool_result_with_metrics",
    "create_legroom_mcp_proxy",
    "DEFAULT_MCP_PROFILES",
    # Agno
    "LegroomAgnoModel",
    "LegroomPreHook",
    "LegroomPostHook",
    "agno_available",
    "create_legroom_hooks",
    "get_agno_provider",
    "get_model_name_from_agno",
    "AgnoOptimizationMetrics",
    "optimize_agno_messages",
    # CrewAI
    "CrewAIToolWrapper",
    "CrewAIToolCompressionMetrics",
    "CrewAIToolMetricsCollector",
    "wrap_crewai_tools",
    "get_crewai_tool_metrics",
    "reset_crewai_tool_metrics",
    # AutoGen
    "AutoGenToolWrapper",
    "AutoGenToolCompressionMetrics",
    "AutoGenToolMetricsCollector",
    "wrap_autogen_tools",
    "get_autogen_tool_metrics",
    "reset_autogen_tool_metrics",
]
