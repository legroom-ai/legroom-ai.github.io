"""Agno integration for Legroom SDK.

This module provides seamless integration with Agno (formerly Phidata),
enabling automatic context optimization for Agno agents.

Components:
1. LegroomAgnoModel - Wraps any Agno model to apply Legroom transforms
2. create_legroom_hooks - Creates pre/post hooks for Agno agents
3. optimize_messages - Standalone function for manual optimization

Example:
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    from legroom.integrations.agno import LegroomAgnoModel

    # Wrap any Agno model
    model = OpenAIChat(id="gpt-4o")
    optimized_model = LegroomAgnoModel(model)

    # Use with agent
    agent = Agent(model=optimized_model)
    response = agent.run("Hello!")
"""

from .hooks import (
    LegroomPostHook,
    LegroomPreHook,
    HookMetrics,
    create_legroom_hooks,
)
from .model import (
    LegroomAgnoModel,
    OptimizationMetrics,
    agno_available,
    optimize_messages,
)
from .providers import get_legroom_provider, get_model_name_from_agno

__all__ = [
    # Model wrapper
    "LegroomAgnoModel",
    "OptimizationMetrics",
    "agno_available",
    "optimize_messages",
    # Hooks
    "create_legroom_hooks",
    "LegroomPreHook",
    "LegroomPostHook",
    "HookMetrics",
    # Provider detection
    "get_legroom_provider",
    "get_model_name_from_agno",
]
