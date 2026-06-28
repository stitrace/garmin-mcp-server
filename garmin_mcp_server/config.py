"""Configuration loaded from environment variables / .env file."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load a .env file from the current working directory if present. This never
# overrides variables already set in the real environment.
load_dotenv(override=False)

logger = logging.getLogger("garmin_mcp_server.config")

DEFAULT_TOKENSTORE = "~/.garminconnect"

# Cache filenames that mark a directory as holding usable credentials: the
# custom garminconnect fork writes ``garmin_tokens.json``; upstream garth uses
# ``oauth1_token.json`` / ``oauth2_token.json``. Any one is enough.
TOKEN_FILE_NAMES = ("garmin_tokens.json", "oauth1_token.json", "oauth2_token.json")


def _expand(path: str) -> str:
    return str(Path(os.path.expanduser(path)))


def _looks_like_token_blob(value: str) -> bool:
    # garminconnect treats a >512-char GARMINTOKENS value as the token JSON blob
    # itself rather than a directory path, so it must not be touched as a path.
    return len(value) > 512


def _dir_has_tokens(path: str) -> bool:
    base = Path(path)
    return any((base / name).is_file() for name in TOKEN_FILE_NAMES)


@dataclass(frozen=True)
class GarminConfig:
    """Runtime configuration for the Garmin client."""

    email: str | None
    password: str | None
    tokenstore: str
    is_cn: bool

    @classmethod
    def from_env(cls) -> GarminConfig:
        # Accept both GARMINTOKENS (garminconnect convention) and
        # GARMIN_TOKEN_DIR (used by some sibling projects) for convenience.
        tokenstore = (
            os.getenv("GARMINTOKENS")
            or os.getenv("GARMIN_TOKEN_DIR")
            or DEFAULT_TOKENSTORE
        )
        is_cn = os.getenv("GARMIN_IS_CN", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return cls(
            email=os.getenv("GARMIN_EMAIL") or None,
            password=os.getenv("GARMIN_PASSWORD") or None,
            tokenstore=cls._resolve_tokenstore(tokenstore),
            is_cn=is_cn,
        )

    @staticmethod
    def _resolve_tokenstore(tokenstore: str) -> str:
        """Resolve the token store, guarding against a stale/misconfigured path.

        A ``GARMINTOKENS`` directory that doesn't exist (or holds no cached
        tokens) would otherwise fall straight through to a credential/MFA login
        that fails in the headless server context. When the default store at
        ``~/.garminconnect`` actually has tokens, prefer it so a working cache
        isn't silently ignored because of a stale override.
        """
        # A long value is the token JSON blob itself, not a path — leave it be.
        if _looks_like_token_blob(tokenstore):
            return tokenstore

        resolved = _expand(tokenstore)
        default_resolved = _expand(DEFAULT_TOKENSTORE)
        if (
            resolved != default_resolved
            and not _dir_has_tokens(resolved)
            and _dir_has_tokens(default_resolved)
        ):
            logger.warning(
                "GARMINTOKENS=%s has no cached tokens; falling back to %s which "
                "does. Update GARMINTOKENS (or re-run garmin-mcp-server-login) "
                "to silence this.",
                resolved,
                default_resolved,
            )
            return default_resolved
        return resolved

    @property
    def has_credentials(self) -> bool:
        return bool(self.email and self.password)
