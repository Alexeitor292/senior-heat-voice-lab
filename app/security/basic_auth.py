import base64
import secrets
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


PUBLIC_PATH_PREFIXES = (
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/twilio",
)

PROTECTED_PATH_PREFIXES = (
    "/ui",
    "/dashboard",
    "/ui-api",
    "/seniors",
    "/calls",
    "/operator-actions",
    "/check-ins",
    "/schedules",
    "/scheduler",
    "/operational-status",
    "/ai-call-sessions",
    "/debug",
)


def _path_matches_prefix(path: str, prefix: str) -> bool:
    if prefix == "/":
        return path == "/"

    return path == prefix or path.startswith(f"{prefix}/")


def _is_public_path(path: str) -> bool:
    return any(
        _path_matches_prefix(path, prefix)
        for prefix in PUBLIC_PATH_PREFIXES
    )


def _is_protected_path(path: str) -> bool:
    return any(
        _path_matches_prefix(path, prefix)
        for prefix in PROTECTED_PATH_PREFIXES
    )


def _unauthorized_response() -> Response:
    return Response(
        content="Authentication required.",
        status_code=401,
        headers={
            "WWW-Authenticate": 'Basic realm="Senior Heat Voice Lab"',
        },
    )


def _credentials_are_valid(authorization_header: str | None) -> bool:
    if not authorization_header:
        return False

    scheme, _, encoded_credentials = authorization_header.partition(" ")

    if scheme.lower() != "basic" or not encoded_credentials:
        return False

    try:
        decoded = base64.b64decode(encoded_credentials).decode("utf-8")
    except Exception:
        return False

    username, separator, password = decoded.partition(":")

    if separator != ":":
        return False

    username_matches = secrets.compare_digest(
        username,
        settings.admin_username,
    )

    password_matches = secrets.compare_digest(
        password,
        settings.admin_password,
    )

    return username_matches and password_matches


class BasicDashboardAuthMiddleware(BaseHTTPMiddleware):
    """
    Protects the dashboard UI and operational API routes.

    This intentionally does not protect /twilio routes because Twilio needs
    to reach those webhooks publicly through ngrok. Twilio routes are protected
    separately by Twilio signature validation.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not settings.dashboard_auth_enabled:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        if _is_public_path(path):
            return await call_next(request)

        if not _is_protected_path(path):
            return await call_next(request)

        authorization_header = request.headers.get("Authorization")

        if not _credentials_are_valid(authorization_header):
            return _unauthorized_response()

        return await call_next(request)