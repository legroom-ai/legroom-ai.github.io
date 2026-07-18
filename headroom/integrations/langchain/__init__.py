"""LangChain integration for Legroom.

This package provides seamless integration with LangChain, including:
- LegroomChatModel: Drop-in wrapper for any LangChain chat model
- LegroomChatMessageHistory: Automatic conversation compression
- LegroomDocumentCompressor: Relevance-based document filtering
- LegroomToolWrapper: Tool output compression for agents
- StreamingMetricsTracker: Token counting during streaming
- LegroomLangSmithCallbackHandler: LangSmith trace enrichment
- compress_tool_messages: LangGraph pre-model hook for ToolMessage compression
- create_compress_tool_messages_node: LangGraph node factory

Example:
    from langchain_openai import ChatOpenAI
    from legroom.integrations.langchain import LegroomChatModel

    # Wrap any LangChain model
    llm = LegroomChatModel(ChatOpenAI(model="gpt-4o"))

    # Use like normal - optimization happens automatically
    response = llm.invoke("Hello!")

Install: pip install legroom[langchain]
"""

# Agent tool wrapping
from .agents import (
    LegroomToolWrapper,
    ToolCompressionMetrics,
    ToolMetricsCollector,
    get_tool_metrics,
    reset_tool_metrics,
    wrap_tools_with_legroom,
)

# Core chat model wrapper
from .chat_model import (
    LegroomCallbackHandler,
    LegroomChatModel,
    LegroomRunnable,
    OptimizationMetrics,
    langchain_available,
    optimize_messages,
)

# LangGraph integration
from .langgraph import (
    CompressToolMessagesConfig,
    CompressToolMessagesResult,
    ToolMessageCompressionMetrics,
    compress_tool_messages,
    create_compress_tool_messages_node,
)

# LangSmith integration
from .langsmith import (
    LegroomLangSmithCallbackHandler,
    is_langsmith_available,
    is_langsmith_tracing_enabled,
)

# Memory integration
from .memory import LegroomChatMessageHistory

# Provider auto-detection
from .providers import (
    detect_provider,
    get_legroom_provider,
    get_model_name_from_langchain,
)

# Retriever integration
from .retriever import CompressionMetrics, LegroomDocumentCompressor

# Streaming metrics
from .streaming import (
    StreamingMetrics,
    StreamingMetricsCallback,
    StreamingMetricsTracker,
    track_async_streaming_response,
    track_streaming_response,
)

__all__ = [
    # Core
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
    # LangGraph
    "compress_tool_messages",
    "create_compress_tool_messages_node",
    "CompressToolMessagesConfig",
    "CompressToolMessagesResult",
    "ToolMessageCompressionMetrics",
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
]
