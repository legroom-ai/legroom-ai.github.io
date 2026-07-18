"""CrewAI integration for Legroom.

This module provides tool output compression for CrewAI agents,
wrapping BaseTool instances so their outputs are automatically
compressed before entering the agent's LLM context.

Components:
    - LegroomToolWrapper: Wraps a single CrewAI BaseTool with compression
    - wrap_tools_with_legroom: Wraps multiple tools at once
    - ToolCompressionMetrics: Per-invocation metrics dataclass
    - ToolMetricsCollector: Aggregates metrics across all invocations

Example:
    from crewai import Agent, Crew, Task
    from crewai.tools.base_tool import tool
    from legroom.integrations.crewai import wrap_tools_with_legroom

    @tool
    def search_db(query: str) -> str:
        \"\"\"Search the database.\"\"\"
        return json.dumps(results)

    wrapped = wrap_tools_with_legroom([search_db])
    agent = Agent(role="Researcher", tools=wrapped, ...)

Install: pip install legroom-ai crewai
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
