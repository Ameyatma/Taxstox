"""Google OAuth ID Token Verifier — Thin adapter around google-auth library.

Performs full OpenID Connect verification per Google's specification:
- RSA signature verification against Google's JWKS endpoint
- iss (issuer) validation
- aud (audience) validation
- exp (expiry) validation
- iat (issued-at) validation (via clock skew)
- azp (authorized party) validation when present

The google-auth library handles JWKS fetching, caching, key rotation,
and all edge cases. This adapter provides a clean interface consistent
with the rest of the codebase.

Traceability: PR1.1 (Google OAuth — JWKS signature verification)
"""

from __future__ import annotations

import logging
import os

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

logger = logging.getLogger(__name__)

_GOOGLE_CLIENT_ID = os.environ.get(
    "GOOGLE_CLIENT_ID",
    "435349196142-bjmgv3b08drd7gag81ps7g5gob407v3j.apps.googleusercontent.com",
)


def verify_google_id_token(token: str) -> dict:
    """Verify a Google ID token and return the verified payload.

    Delegates to google-auth library for all cryptographic verification,
    JWKS fetching, and claim validation.

    Args:
        token: The raw Google ID token (JWT) from the client

    Returns:
        Verified token payload dict with keys: sub, email, name, aud, iss, exp

    Raises:
        ValueError: If the token is invalid, expired, forged, wrong audience,
                    wrong issuer, or otherwise fails verification.
    """
    try:
        payload = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            _GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
        return payload

    except ValueError as e:
        logger.warning(
            "Google token verification failed",
            extra={"reason": str(e)[:200]},
        )
        raise


def get_client_id() -> str:
    """Return the configured Google OAuth client ID."""
    return _GOOGLE_CLIENT_ID
