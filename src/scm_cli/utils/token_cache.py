"""OAuth token file cache for scm-cli.

Fetching an OAuth token (plus the JWKS signing key) adds network roundtrips
to every CLI invocation. Tokens are therefore cached per context under
``~/.scm-cli/cache/`` and reused until shortly before expiry, so consecutive
commands skip authentication entirely.

Cache entries also record the client_id and tsg_id the token was issued for:
commit operations need an admin identity when running on a cached token
(bearer-mode session), and a context switch must not reuse another tenant's
token.

Set ``SCM_NO_TOKEN_CACHE=1`` to disable the cache entirely.
"""

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.expanduser("~/.scm-cli/cache")

# Refuse to reuse tokens within this many seconds of expiry (matches the
# SDK's own TOKEN_EXPIRY_BUFFER).
EXPIRY_BUFFER_SECONDS = 300


def _cache_disabled() -> bool:
    return os.environ.get("SCM_NO_TOKEN_CACHE", "").strip().lower() in ("1", "true", "yes", "on")


def _cache_path(context_name: str | None) -> str:
    return os.path.join(CACHE_DIR, f"token-{context_name or 'default'}.json")


def save_token(context_name: str | None, token: dict[str, Any], client_id: str, tsg_id: str) -> None:
    """Persist an OAuth token for a context (0600 file permissions)."""
    if _cache_disabled():
        return
    try:
        os.makedirs(CACHE_DIR, mode=0o700, exist_ok=True)
        path = _cache_path(context_name)
        entry = {"token": token, "client_id": client_id, "tsg_id": tsg_id}
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(entry, f)
        logger.debug(f"Cached OAuth token for context '{context_name or 'default'}'")
    except OSError as e:
        # Cache failures must never break the CLI.
        logger.debug(f"Could not write token cache: {e}")


def load_token(context_name: str | None) -> dict[str, Any] | None:
    """Return the cached entry for a context, or None if absent/expired/corrupt.

    The returned dict has keys ``token`` (the OAuth token dict), ``client_id``,
    and ``tsg_id``.
    """
    if _cache_disabled():
        return None
    path = _cache_path(context_name)
    try:
        with open(path) as f:
            entry = json.load(f)
        expires_at = float(entry["token"]["expires_at"])
        if expires_at - EXPIRY_BUFFER_SECONDS <= time.time():
            logger.debug(f"Cached token for '{context_name or 'default'}' expired")
            clear_token(context_name)
            return None
        if not entry["token"].get("access_token"):
            raise KeyError("access_token")
        return entry
    except FileNotFoundError:
        return None
    except (KeyError, TypeError, ValueError, OSError) as e:
        logger.debug(f"Discarding unusable token cache ({e})")
        clear_token(context_name)
        return None


def clear_token(context_name: str | None) -> None:
    """Delete the cached token for a context (no-op if absent)."""
    import contextlib

    with contextlib.suppress(OSError):
        os.remove(_cache_path(context_name))
