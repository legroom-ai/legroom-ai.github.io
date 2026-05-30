from __future__ import annotations

import hashlib


def derive_session_key(
    *, credential: str | None, conversation_scope: str | None, salt: bytes
) -> str:
    """Pinned session_key derivation. Every host MUST call this so the proxy and any
    embedded adapter key CCR/session/drift state identically. The raw credential is
    hashed, never stored. A falsy ``conversation_scope`` (None or "") yields a
    tenant-scoped key (session == tenant)."""
    tenant_principal = hashlib.sha256(salt + (credential or "").encode()).hexdigest()
    scope = conversation_scope or tenant_principal
    return hashlib.sha256(f"{tenant_principal}:{scope}".encode()).hexdigest()
