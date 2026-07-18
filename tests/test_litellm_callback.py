"""Tests for LegroomCallback LiteLLM integration.

Regression for #1114: LegroomCallback did not inherit CustomLogger, so any
hook LiteLLM added post-1.89.x (e.g. async_post_call_success_hook) raised
AttributeError and crashed the LiteLLM proxy.
"""

from __future__ import annotations

import asyncio

from tests._dotenv import importorskip_no_env_leak

importorskip_no_env_leak("litellm")

from legroom.integrations.litellm_callback import LegroomCallback  # noqa: E402


class TestLegroomCallbackCustomLoggerInheritance:
    def test_instantiates_without_error(self) -> None:
        cb = LegroomCallback()
        assert cb is not None

    def test_has_async_post_call_success_hook(self) -> None:
        """Regression: AttributeError: 'LegroomCallback' has no attr 'async_post_call_success_hook'."""
        cb = LegroomCallback()
        assert hasattr(cb, "async_post_call_success_hook"), (
            "async_post_call_success_hook must exist (added in litellm 1.89.x)"
        )

    def test_async_post_call_success_hook_is_callable(self) -> None:
        """LiteLLM must be able to await the hook without exception."""
        cb = LegroomCallback()
        hook = cb.async_post_call_success_hook
        assert callable(hook)

    def test_async_post_call_success_hook_does_not_raise(self) -> None:
        """Calling the hook (no-op from CustomLogger) must not raise."""
        cb = LegroomCallback()

        async def _run() -> None:
            await cb.async_post_call_success_hook(
                data={"model": "gpt-4o", "messages": []},
                user_api_key_dict={},
                response=None,
            )

        asyncio.run(_run())

    def test_all_current_litellm_async_hooks_present(self) -> None:
        """LegroomCallback must expose every async hook CustomLogger defines."""
        from litellm.integrations.custom_logger import CustomLogger

        cb = LegroomCallback()
        missing = [
            name
            for name in dir(CustomLogger)
            if name.startswith("async_") and not hasattr(cb, name)
        ]
        assert not missing, f"Missing CustomLogger hooks: {missing}"

    def test_async_pre_call_hook_still_works(self) -> None:
        """Inheritance must not break the existing compression hook."""
        cb = LegroomCallback()
        assert hasattr(cb, "async_pre_call_hook")
        assert callable(cb.async_pre_call_hook)

    def test_total_tokens_saved_property(self) -> None:
        cb = LegroomCallback()
        assert cb.total_tokens_saved == 0
