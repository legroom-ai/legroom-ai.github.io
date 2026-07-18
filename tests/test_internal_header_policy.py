from __future__ import annotations

import pytest

from legroom.proxy.internal_header_policy import (
    STRIP_INTERNAL_HEADERS_ENV,
    resolve_strip_internal_headers_mode,
    strip_internal_headers,
)


def test_resolve_strip_internal_headers_mode_defaults_to_enabled() -> None:
    assert resolve_strip_internal_headers_mode(None) == "enabled"
    assert resolve_strip_internal_headers_mode("  ") == "enabled"


def test_resolve_strip_internal_headers_mode_accepts_known_values() -> None:
    assert resolve_strip_internal_headers_mode("ENABLED") == "enabled"
    assert resolve_strip_internal_headers_mode(" disabled ") == "disabled"


def test_resolve_strip_internal_headers_mode_rejects_unknown_values() -> None:
    with pytest.raises(ValueError, match=STRIP_INTERNAL_HEADERS_ENV):
        resolve_strip_internal_headers_mode("maybe")


def test_strip_internal_headers_removes_legroom_headers_case_insensitively() -> None:
    headers = {
        "Authorization": "Bearer token",
        "x-legroom-bypass": "true",
        "X-Legroom-User-Id": "user-1",
        "content-type": "application/json",
    }

    stripped = strip_internal_headers(headers, mode="enabled")

    assert stripped == {
        "Authorization": "Bearer token",
        "content-type": "application/json",
    }
    assert "x-legroom-bypass" in headers


def test_strip_internal_headers_disabled_returns_copy_unchanged() -> None:
    headers = {"x-legroom-mode": "passthrough", "content-type": "application/json"}

    copied = strip_internal_headers(headers, mode="disabled")

    assert copied == headers
    assert copied is not headers
