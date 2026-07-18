"""Custom exceptions for Legroom.

This module provides explicit exception classes for better error handling
and debugging. All exceptions inherit from LegroomError, making it easy
to catch all Legroom-related errors.

Example:
    from legroom import LegroomClient, LegroomError, ConfigurationError

    try:
        client = LegroomClient(...)
        client.validate_setup()
    except ConfigurationError as e:
        print(f"Configuration problem: {e}")
    except LegroomError as e:
        print(f"Legroom error: {e}")
"""

from __future__ import annotations

from typing import Any


class LegroomError(Exception):
    """Base exception for all Legroom errors.

    All Legroom exceptions inherit from this class, making it easy
    to catch any Legroom-related error:

        try:
            client.chat.completions.create(...)
        except LegroomError as e:
            # Handle any Legroom error
            pass
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class ConfigurationError(LegroomError):
    """Raised when Legroom is misconfigured.

    This includes:
    - Invalid mode values
    - Missing required configuration
    - Incompatible configuration combinations

    Example:
        ConfigurationError(
            "Invalid mode 'foo'",
            details={"valid_modes": ["audit", "optimize"]}
        )
    """

    pass


class ProviderError(LegroomError):
    """Raised when there's an issue with the LLM provider.

    This includes:
    - Provider not recognized
    - Provider-specific configuration issues
    - Token counter errors

    Example:
        ProviderError(
            "Unknown provider",
            details={"provider": "foo", "known_providers": ["openai", "anthropic"]}
        )
    """

    pass


class StorageError(LegroomError):
    """Raised when there's an issue with metrics storage.

    This includes:
    - Database connection failures
    - Invalid storage URL
    - Write failures

    Example:
        StorageError(
            "Cannot connect to database",
            details={"url": "sqlite:///foo.db", "error": "Permission denied"}
        )
    """

    pass


class CompressionError(LegroomError):
    """Raised when compression fails.

    This includes:
    - Parse errors in tool outputs
    - Invalid JSON structures
    - Compression strategy failures

    Example:
        CompressionError(
            "Failed to parse tool output",
            details={"tool_name": "search_api", "content_preview": "..."}
        )
    """

    pass


class TokenizationError(LegroomError):
    """Raised when token counting fails.

    This includes:
    - Unknown model for tokenization
    - Encoding errors
    - Tiktoken/tokenizer loading failures

    Example:
        TokenizationError(
            "Unknown model for tokenization",
            details={"model": "gpt-99", "fallback_used": True}
        )
    """

    pass


class CacheError(LegroomError):
    """Raised when caching operations fail.

    This includes:
    - Cache store errors
    - Retrieval failures
    - CCR (Compress-Cache-Retrieve) errors

    Example:
        CacheError(
            "Cache entry expired",
            details={"hash": "abc123", "ttl": 300}
        )
    """

    pass


class ValidationError(LegroomError):
    """Raised when setup validation fails.

    This is raised by validate_setup() when the configuration
    or environment is not properly set up.

    Example:
        ValidationError(
            "Setup validation failed",
            details={
                "provider_ok": True,
                "storage_ok": False,
                "storage_error": "Cannot write to database"
            }
        )
    """

    pass


class TransformError(LegroomError):
    """Raised when a transform fails to apply.

    This includes:
    - SmartCrusher failures
    - ContentRouter errors
    - Pipeline errors

    Example:
        TransformError(
            "Transform failed",
            details={"transform": "smart_crusher", "reason": "..."}
        )
    """

    pass
