"""Differential network capture reporting for Claude Code vs Legroom.

The capture format is intentionally JSONL so mitmproxy addons, tests, and
future packet capture tools can all produce the same records without a heavy
dependency in the Legroom package.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

logger = logging.getLogger(__name__)

SENSITIVE_HEADER_PARTS = ("authorization", "api-key", "apikey", "token", "secret", "cookie")
SENSITIVE_QUERY_PARTS = ("key", "token", "secret", "signature", "code")
MAX_BODY_PREVIEW_CHARS = 1200


@dataclass(frozen=True)
class CapturedExchange:
    """A sanitized HTTP request/response pair captured by the harness."""

    lane: str
    sequence: int
    method: str
    url: str
    host: str
    path: str
    request_headers: dict[str, str] = field(default_factory=dict)
    response_status: int | None = None
    response_headers: dict[str, str] = field(default_factory=dict)
    request_body_sha256: str | None = None
    request_body_size: int = 0
    request_json: Any | None = None
    request_body_preview: str | None = None

    @property
    def route_key(self) -> str:
        return f"{self.method.upper()} {self.host}{self.path}"

    @property
    def path_key(self) -> str:
        return f"{self.method.upper()} {self.path}"


@dataclass(frozen=True)
class CaptureDiff:
    """Comparison result between a direct lane and a Legroom lane."""

    direct_count: int
    legroom_count: int
    only_direct: list[str]
    only_legroom: list[str]
    paired: list[dict[str, Any]]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "direct_count": self.direct_count,
            "legroom_count": self.legroom_count,
            "only_direct": self.only_direct,
            "only_legroom": self.only_legroom,
            "paired": self.paired,
        }


def _redact_value(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    if not text:
        return text
    return "<redacted>"


def sanitize_headers(headers: dict[str, Any] | None) -> dict[str, str]:
    sanitized: dict[str, str] = {}
    for key, value in (headers or {}).items():
        lower = str(key).lower()
        if any(part in lower for part in SENSITIVE_HEADER_PARTS):
            sanitized[str(key)] = _redact_value(value)
        else:
            sanitized[str(key)] = str(value)
    return sanitized


def sanitize_url(url: str) -> str:
    parsed = urlsplit(url)
    pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if any(part in key.lower() for part in SENSITIVE_QUERY_PARTS):
            pairs.append((key, "<redacted>"))
        else:
            pairs.append((key, value))
    query = urlencode(pairs, doseq=True)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, ""))


def _body_bytes(record: dict[str, Any]) -> bytes:
    body_b64 = record.get("request_body_b64")
    if isinstance(body_b64, str):
        try:
            return base64.b64decode(body_b64, validate=True)
        except Exception:
            return b""
    body = record.get("request_body")
    if isinstance(body, str):
        return body.encode("utf-8", errors="replace")
    return b""


def _parse_json_body(body: bytes) -> Any | None:
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


def _preview_body(body: bytes) -> str | None:
    if not body:
        return None
    text = body[:MAX_BODY_PREVIEW_CHARS].decode("utf-8", errors="replace")
    return text.replace("\r\n", "\n")


def exchange_from_record(
    record: dict[str, Any], *, fallback_lane: str, sequence: int
) -> CapturedExchange:
    url = sanitize_url(str(record.get("url") or ""))
    parsed = urlsplit(url)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    body = _body_bytes(record)
    request_json = record.get("request_json")
    if request_json is None:
        request_json = _parse_json_body(body)
    body_sha = record.get("request_body_sha256")
    if body_sha is None and body:
        body_sha = hashlib.sha256(body).hexdigest()
    return CapturedExchange(
        lane=str(record.get("lane") or fallback_lane),
        sequence=int(record.get("sequence") or sequence),
        method=str(record.get("method") or "GET").upper(),
        url=url,
        host=parsed.netloc or str(record.get("host") or ""),
        path=path,
        request_headers=sanitize_headers(record.get("request_headers")),
        response_status=record.get("response_status"),
        response_headers=sanitize_headers(record.get("response_headers")),
        request_body_sha256=str(body_sha) if body_sha else None,
        request_body_size=int(record.get("request_body_size") or len(body)),
        request_json=request_json,
        request_body_preview=_preview_body(body),
    )


def load_capture_file(path: str | Path, *, fallback_lane: str) -> list[CapturedExchange]:
    """Load a JSONL capture file produced by the mitmproxy addon."""

    exchanges: list[CapturedExchange] = []
    capture_path = Path(path)
    skipped = 0
    for line_number, line in enumerate(capture_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        # mitmproxy captures can be truncated mid-write; skip a corrupt line
        # rather than aborting the whole diff with a raw JSONDecodeError.
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        exchanges.append(
            exchange_from_record(record, fallback_lane=fallback_lane, sequence=line_number)
        )
    if skipped:
        logger.warning("Skipped %d malformed line(s) in capture file %s", skipped, capture_path)
    return exchanges


def _json_paths(value: Any, prefix: str = "$") -> dict[str, Any]:
    if isinstance(value, dict):
        paths: dict[str, Any] = {}
        for key, child in sorted(value.items()):
            paths.update(_json_paths(child, f"{prefix}.{key}"))
        return paths or {prefix: {}}
    if isinstance(value, list):
        paths = {}
        for index, child in enumerate(value):
            paths.update(_json_paths(child, f"{prefix}[{index}]"))
        return paths or {prefix: []}
    return {prefix: value}


def _header_delta(
    direct: dict[str, str], legroom: dict[str, str]
) -> tuple[list[str], list[str], list[str]]:
    direct_keys = {key.lower(): key for key in direct}
    legroom_keys = {key.lower(): key for key in legroom}
    only_direct = sorted(direct_keys[key] for key in set(direct_keys) - set(legroom_keys))
    only_legroom = sorted(legroom_keys[key] for key in set(legroom_keys) - set(direct_keys))
    changed: list[str] = []
    for lower in sorted(set(direct_keys) & set(legroom_keys)):
        d_key = direct_keys[lower]
        h_key = legroom_keys[lower]
        if direct[d_key] != legroom[h_key]:
            changed.append(d_key)
    return only_direct, only_legroom, changed


def _header_value(headers: dict[str, str], name: str) -> str | None:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


def _anthropic_request_summary(exchange: CapturedExchange) -> dict[str, Any]:
    request_json = exchange.request_json if isinstance(exchange.request_json, dict) else {}
    tools = request_json.get("tools")
    tool_count = len(tools) if isinstance(tools, list) else 0
    tool_bytes = (
        len(json.dumps(tools, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        if isinstance(tools, list)
        else 0
    )
    return {
        "anthropic_beta": _header_value(exchange.request_headers, "anthropic-beta"),
        "tools_count": tool_count,
        "tools_bytes": tool_bytes,
    }


def _pair_exchanges(
    direct: list[CapturedExchange], legroom: list[CapturedExchange], *, pair_by: str = "path"
) -> tuple[list[tuple[CapturedExchange, CapturedExchange]], list[str], list[str]]:
    direct_by_key: dict[str, list[CapturedExchange]] = {}
    legroom_by_key: dict[str, list[CapturedExchange]] = {}
    for item in direct:
        key = item.route_key if pair_by == "route" else item.path_key
        direct_by_key.setdefault(key, []).append(item)
    for item in legroom:
        key = item.route_key if pair_by == "route" else item.path_key
        legroom_by_key.setdefault(key, []).append(item)

    pairs: list[tuple[CapturedExchange, CapturedExchange]] = []
    only_direct: list[str] = []
    only_legroom: list[str] = []
    for key in sorted(set(direct_by_key) | set(legroom_by_key)):
        direct_items = direct_by_key.get(key, [])
        legroom_items = legroom_by_key.get(key, [])
        shared = min(len(direct_items), len(legroom_items))
        pairs.extend(zip(direct_items[:shared], legroom_items[:shared], strict=False))
        only_direct.extend([item.route_key for item in direct_items[shared:]])
        only_legroom.extend([item.route_key for item in legroom_items[shared:]])
    return pairs, only_direct, only_legroom


def compare_captures(
    direct: list[CapturedExchange], legroom: list[CapturedExchange], *, pair_by: str = "path"
) -> CaptureDiff:
    pairs, only_direct, only_legroom = _pair_exchanges(direct, legroom, pair_by=pair_by)
    paired: list[dict[str, Any]] = []
    for direct_item, legroom_item in pairs:
        direct_paths = (
            _json_paths(direct_item.request_json) if direct_item.request_json is not None else {}
        )
        legroom_paths = (
            _json_paths(legroom_item.request_json)
            if legroom_item.request_json is not None
            else {}
        )
        only_direct_json = sorted(set(direct_paths) - set(legroom_paths))
        only_legroom_json = sorted(set(legroom_paths) - set(direct_paths))
        changed_json = sorted(
            path
            for path in set(direct_paths) & set(legroom_paths)
            if direct_paths[path] != legroom_paths[path]
        )
        headers_only_direct, headers_only_legroom, headers_changed = _header_delta(
            direct_item.request_headers, legroom_item.request_headers
        )
        paired.append(
            {
                "route": direct_item.route_key,
                "legroom_route": legroom_item.route_key,
                "direct_sequence": direct_item.sequence,
                "legroom_sequence": legroom_item.sequence,
                "status": {
                    "direct": direct_item.response_status,
                    "legroom": legroom_item.response_status,
                },
                "request_body_size": {
                    "direct": direct_item.request_body_size,
                    "legroom": legroom_item.request_body_size,
                    "delta": legroom_item.request_body_size - direct_item.request_body_size,
                },
                "request_body_sha256": {
                    "direct": direct_item.request_body_sha256,
                    "legroom": legroom_item.request_body_sha256,
                    "same": direct_item.request_body_sha256 == legroom_item.request_body_sha256,
                },
                "anthropic": {
                    "direct": _anthropic_request_summary(direct_item),
                    "legroom": _anthropic_request_summary(legroom_item),
                },
                "headers": {
                    "only_direct": headers_only_direct,
                    "only_legroom": headers_only_legroom,
                    "changed": headers_changed,
                },
                "json": {
                    "only_direct": only_direct_json,
                    "only_legroom": only_legroom_json,
                    "changed": changed_json,
                },
            }
        )
    return CaptureDiff(
        direct_count=len(direct),
        legroom_count=len(legroom),
        only_direct=only_direct,
        only_legroom=only_legroom,
        paired=paired,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _list_or_dash(values: list[str]) -> str:
    return ", ".join(values) if values else "-"


def render_markdown_report(diff: CaptureDiff) -> str:
    lines = [
        "# Differential Network Capture Report",
        "",
        f"Generated: `{diff.generated_at}`",
        "",
        "## Summary",
        "",
        f"- Direct exchanges: `{diff.direct_count}`",
        f"- Legroom exchanges: `{diff.legroom_count}`",
        f"- Paired exchanges: `{len(diff.paired)}`",
        f"- Only direct: `{len(diff.only_direct)}`",
        f"- Only Legroom: `{len(diff.only_legroom)}`",
        "",
    ]
    if diff.only_direct:
        lines.extend(["## Only Direct", "", *[f"- `{route}`" for route in diff.only_direct], ""])
    if diff.only_legroom:
        lines.extend(
            ["## Only Legroom", "", *[f"- `{route}`" for route in diff.only_legroom], ""]
        )

    lines.extend(
        [
            "## Paired Exchanges",
            "",
            "| Route | Status | Body Bytes | Body SHA | Header Delta | JSON Delta |",
            "| --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for item in diff.paired:
        route = item["route"]
        if item.get("legroom_route") and item["legroom_route"] != route:
            route = f"{route} -> {item['legroom_route']}"
        status = f"{item['status']['direct']} -> {item['status']['legroom']}"
        sizes = item["request_body_size"]
        body = f"{sizes['direct']} -> {sizes['legroom']} ({sizes['delta']:+})"
        sha = "same" if item["request_body_sha256"]["same"] else "changed"
        headers = item["headers"]
        header_delta = (
            f"+{_list_or_dash(headers['only_legroom'])}; "
            f"-{_list_or_dash(headers['only_direct'])}; "
            f"changed={_list_or_dash(headers['changed'])}"
        )
        json_delta = item["json"]
        json_text = (
            f"+{_list_or_dash(json_delta['only_legroom'])}; "
            f"-{_list_or_dash(json_delta['only_direct'])}; "
            f"changed={_list_or_dash(json_delta['changed'])}"
        )
        anthropic = item.get("anthropic", {})
        direct_anthropic = anthropic.get("direct", {})
        legroom_anthropic = anthropic.get("legroom", {})
        tool_delta = legroom_anthropic.get("tools_bytes", 0) - direct_anthropic.get(
            "tools_bytes", 0
        )
        json_text = (
            f"{json_text}; tools={direct_anthropic.get('tools_count', 0)}"
            f"->{legroom_anthropic.get('tools_count', 0)}"
            f" ({tool_delta:+} bytes)"
        )
        lines.append(
            f"| `{route}` | `{status}` | `{body}` | `{sha}` | {header_delta} | {json_text} |"
        )
    lines.append("")
    return "\n".join(lines)
