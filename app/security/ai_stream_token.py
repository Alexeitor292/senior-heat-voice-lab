from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class AIStreamTokenClaims:
    senior_id: int
    expires_at: int
    nonce: str


def _token_secret() -> str:
    """
    Use a dedicated AI stream token secret when configured.

    Falls back to the Twilio auth token so local development works without
    another required secret. Production should prefer AI_STREAM_TOKEN_SECRET.
    """

    secret = settings.ai_stream_token_secret or settings.twilio_auth_token

    if not secret:
        raise RuntimeError(
            "AI stream token signing requires AI_STREAM_TOKEN_SECRET or TWILIO_AUTH_TOKEN."
        )

    return secret


def _sign(payload: str) -> str:
    return hmac.new(
        _token_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_ai_stream_token(
    senior_id: int,
    *,
    expires_in_seconds: int | None = None,
    now: float | None = None,
) -> str:
    issued_at = int(now if now is not None else time.time())
    ttl = expires_in_seconds or settings.ai_stream_token_ttl_seconds
    expires_at = issued_at + ttl
    nonce = secrets.token_urlsafe(16)

    payload = f"{senior_id}.{expires_at}.{nonce}"
    signature = _sign(payload)

    return f"{payload}.{signature}"


def verify_ai_stream_token(
    token: str | None,
    *,
    now: float | None = None,
) -> AIStreamTokenClaims | None:
    if not token:
        return None

    parts = token.split(".")

    if len(parts) != 4:
        return None

    senior_id_raw, expires_at_raw, nonce, supplied_signature = parts

    try:
        senior_id = int(senior_id_raw)
        expires_at = int(expires_at_raw)
    except ValueError:
        return None

    if senior_id <= 0:
        return None

    if not nonce:
        return None

    current_time = int(now if now is not None else time.time())

    if expires_at < current_time:
        return None

    payload = f"{senior_id}.{expires_at}.{nonce}"
    expected_signature = _sign(payload)

    if not hmac.compare_digest(supplied_signature, expected_signature):
        return None

    return AIStreamTokenClaims(
        senior_id=senior_id,
        expires_at=expires_at,
        nonce=nonce,
    )