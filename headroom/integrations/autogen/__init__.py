"""AutoGen integration for Legroom.

This module provides tool output compression for AutoGen agents,
wrapping FunctionTool instances so their outputs are automatically
compressed before entering the agent's model context.

Components:
    - LegroomToolWrapper: Wraps a single AutoGen FunctionTool with compression
    - wrap_tools_with_legroom: Wraps multiple tools at once
    - ToolCompressionMetrics: Per-invocation metrics dataclass
    - ToolMetricsCollector: Aggregates metrics across all invocations

Example:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_core.tools import FunctionTool
    from legroom.integrations.autogen import wrap_tools_with_legroom

    def search_db(query: str) -> str:
        return json.dumps(results)

    tool = FunctionTool(search_db, description="Search the database")
    wrapped = wrap_tools_with_legroom([tool])

    agent = AssistantAgent(name="researcher", tools=wrapped, ...)

Install: pip install legroom-ai autogen-agentchat
"""

from .agents import (
    LegroomToolWrapper,
    ToolCompressionMetrics,
    ToolMetricsCollector,
    get_tool_metrics,
    reset_tool_metrics,
    wrap_tools_with_legroom,
)

__all__ = [
    "LegroomToolWrapper",
    "ToolCompressionMetrics",
    "ToolMetricsCollector",
    "wrap_tools_with_legroom",
    "get_tool_metrics",
    "reset_tool_metrics",
]
