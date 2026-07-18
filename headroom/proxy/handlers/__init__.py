"""Handler mixins for LegroomProxy.

Each mixin class contains methods extracted from LegroomProxy that handle
requests for a specific provider or concern. The mixins rely on LegroomProxy's
__init__ for all self.* attributes (duck typing).
"""

from legroom.proxy.handlers.anthropic import AnthropicHandlerMixin
from legroom.proxy.handlers.batch import BatchHandlerMixin
from legroom.proxy.handlers.bedrock import BedrockHandlerMixin
from legroom.proxy.handlers.gemini import GeminiHandlerMixin
from legroom.proxy.handlers.openai import OpenAIHandlerMixin
from legroom.proxy.handlers.streaming import StreamingMixin

__all__ = [
    "AnthropicHandlerMixin",
    "BatchHandlerMixin",
    "BedrockHandlerMixin",
    "GeminiHandlerMixin",
    "OpenAIHandlerMixin",
    "StreamingMixin",
]
