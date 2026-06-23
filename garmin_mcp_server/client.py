"""Lazy, resilient wrapper around the ``garminconnect.Garmin`` client.

Authentication strategy (in priority order):

1. **Cached OAuth tokens** (recommended). Created once via ``garmin-mcp-server-login``
   and stored in ``GARMINTOKENS`` (default ``~/.garminconnect``). No password is
   needed at runtime and MFA is handled during the one-time login.
2. **Email + password** from the environment. Only works when the account does
   not require MFA. On success the resulting tokens are cached for next time.

The client logs in lazily on first use and transparently re-authenticates once
if a request fails because the session expired.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

from garminconnect import Garmin, GarminConnectAuthenticationError

from .config import GarminConfig

logger = logging.getLogger("garmin_mcp_server.client")


class GarminAuthError(RuntimeError):
    """Raised when the server cannot authenticate with Garmin Connect."""


class GarminClient:
    """Thread-safe, lazily-authenticated Garmin Connect client."""

    def __init__(self, config: GarminConfig | None = None) -> None:
        self._config = config or GarminConfig.from_env()
        self._client: Garmin | None = None
        self._lock = threading.RLock()
        self._profile_number: str | None = None

    # -- authentication ----------------------------------------------------

    def _login(self) -> Garmin:
        """Authenticate with Garmin Connect.

        Delegates to garminconnect's own ``login()``, which transparently:
          * loads cached tokens from the token-store directory,
          * accepts a DI token JSON blob (when ``GARMINTOKENS`` holds the token
            string itself rather than a path),
          * refreshes an expiring DI token without a full re-login,
          * falls back to email/password and then persists fresh tokens.
        """
        cfg = self._config
        client = Garmin(email=cfg.email, password=cfg.password, is_cn=cfg.is_cn)
        try:
            client.login(cfg.tokenstore)
            logger.info("Authenticated with Garmin Connect (tokenstore=%s)", cfg.tokenstore)
            return client
        except GarminConnectAuthenticationError as exc:
            if not cfg.has_credentials:
                raise GarminAuthError(
                    "No valid Garmin tokens found and no GARMIN_EMAIL/GARMIN_PASSWORD set.\n"
                    "Run `garmin-mcp-server-login` once to create cached tokens (this also "
                    "handles multi-factor authentication)."
                ) from exc
            raise GarminAuthError(
                f"Garmin authentication failed: {exc}. If your account uses MFA, "
                f"run `garmin-mcp-server-login` to authenticate interactively."
            ) from exc
        except Exception as exc:  # pragma: no cover - network/edge errors
            raise GarminAuthError(f"Unexpected error during Garmin login: {exc}") from exc

    @property
    def raw(self) -> Garmin:
        """Return the underlying authenticated ``Garmin`` client (logging in if needed)."""
        with self._lock:
            if self._client is None:
                self._client = self._login()
            return self._client

    def _reauth(self) -> Garmin:
        with self._lock:
            self._client = self._login()
            return self._client

    # -- invocation --------------------------------------------------------

    # Exceptions that indicate an expired/invalid session and are worth one
    # re-authentication attempt. garminconnect (>=0.3) raises
    # ``GarminConnectAuthenticationError`` on a 401; the ``Garth*`` names are
    # retained defensively for older installs that still surfaced the (now
    # deprecated) garth transport errors. Matched by class name rather than
    # identity so import order can't break the comparison.
    _AUTH_ERROR_NAMES = frozenset(
        {"GarminConnectAuthenticationError", "GarthHTTPError", "GarthException"}
    )

    @classmethod
    def _is_auth_error(cls, exc: BaseException) -> bool:
        return type(exc).__name__ in cls._AUTH_ERROR_NAMES

    def call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Call a method on the Garmin client, re-authenticating once on auth failure."""
        fn: Callable[..., Any] = getattr(self.raw, method)
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if not self._is_auth_error(exc):
                raise
            logger.warning("Call to %s failed (%s); retrying after re-auth", method, exc)
            fn = getattr(self._reauth(), method)
            return fn(*args, **kwargs)

    # -- convenience -------------------------------------------------------

    def profile_number(self) -> str:
        """Resolve and cache the user's profile number (needed for gear endpoints)."""
        if self._profile_number is None:
            profile = self.call("get_user_profile")
            number = (
                profile.get("userProfileNumber")
                or profile.get("profileId")
                or profile.get("id")
            )
            if number is None:
                raise GarminAuthError("Could not resolve user profile number from profile data.")
            self._profile_number = str(number)
        return self._profile_number
