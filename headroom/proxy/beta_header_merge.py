"""Deterministic merge helpers for provider beta request headers."""

from __future__ import annotations


def split_beta_tokens(value: str | None) -> list[str]:
    """Split a comma-separated beta-header value into trimmed tokens."""

    if not value:
        return []
    out: list[str] = []
    for raw in value.split(","):
        token = raw.strip()
        if token:
            out.append(token)
    return out


def merge_beta_tokens(client_value: str | None, legroom_required: list[str]) -> str:
    """Merge client beta tokens with Legroom-required tokens deterministically."""

    seen_lower: set[str] = set()
    out: list[str] = []
    for token in split_beta_tokens(client_value):
        lower = token.lower()
        if lower in seen_lower:
            continue
        seen_lower.add(lower)
        out.append(token)
    for token in legroom_required:
        if not token:
            continue
        token = token.strip()
        if not token:
            continue
        lower = token.lower()
        if lower in seen_lower:
            continue
        seen_lower.add(lower)
        out.append(token)
    return ",".join(out)


def merge_anthropic_beta(client_value: str | None, legroom_required: list[str]) -> str:
    """Merge client anthropic-beta value with Legroom-required tokens."""

    return merge_beta_tokens(client_value, legroom_required)


def merge_openai_beta(client_value: str | None, legroom_required: list[str]) -> str:
    """Merge client OpenAI-Beta value with Legroom-required tokens."""

    return merge_beta_tokens(client_value, legroom_required)
