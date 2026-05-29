from urllib.parse import parse_qsl

from starlette.types import ASGIApp, Message, Receive, Scope, Send
from twilio.request_validator import RequestValidator

from app.config import settings
from app.utils.safe_logging import safe_log_event


def _is_twilio_path(path: str) -> bool:
    return path == "/twilio" or path.startswith("/twilio/")


def _build_candidate_urls(scope: Scope, headers: dict[str, str]) -> list[str]:
    """
    Returns candidate URLs to try for Twilio signature validation,
    in priority order with duplicates removed.

    Twilio signs the public URL it called. Behind ngrok/proxies the
    Host header or forwarded headers may differ from PUBLIC_BASE_URL,
    so we try all plausible reconstructions.
    """
    path = scope.get("path", "")
    query_string = scope.get("query_string", b"").decode("utf-8")
    suffix = path + (f"?{query_string}" if query_string else "")

    candidates: list[str] = []

    # 1. PUBLIC_BASE_URL from config (highest priority — set to the ngrok URL)
    candidates.append(f"{settings.public_base_url.rstrip('/')}{suffix}")

    # 2. x-forwarded-proto + x-forwarded-host (set by ngrok / reverse proxies)
    forwarded_proto = headers.get("x-forwarded-proto")
    forwarded_host = headers.get("x-forwarded-host")
    if forwarded_proto and forwarded_host:
        candidates.append(f"{forwarded_proto}://{forwarded_host}{suffix}")

    # 3. Host header with forwarded proto (or https fallback)
    host = headers.get("host")
    if host:
        proto = forwarded_proto or "https"
        candidates.append(f"{proto}://{host}{suffix}")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for url in candidates:
        if url not in seen:
            seen.add(url)
            unique.append(url)

    return unique


def _parse_form_params(body: bytes) -> dict[str, str]:
    pairs = parse_qsl(
        body.decode("utf-8"),
        keep_blank_values=True,
    )
    return {key: value for key, value in pairs}


class TwilioSignatureValidationMiddleware:
    """
    Validates Twilio signatures for /twilio/* routes.

    This is implemented as ASGI middleware so we can read the request body
    for validation and then replay the body to FastAPI route handlers.
    """

    def __init__(self, app: ASGIApp):
        self.app = app
        self.validator = RequestValidator(settings.twilio_auth_token)

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        if (
            not settings.twilio_signature_validation_enabled
            or not _is_twilio_path(path)
        ):
            await self.app(scope, receive, send)
            return

        body = b""
        more_body = True

        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }

        signature = headers.get("x-twilio-signature")
        params = _parse_form_params(body)
        candidate_urls = _build_candidate_urls(scope, headers)

        is_valid = any(
            self.validator.validate(url, params, signature or "")
            for url in candidate_urls
        )

        if not is_valid:
            blank_keys = [k for k, v in params.items() if v == ""]

            safe_log_event(
                "Invalid Twilio Signature",
                {
                    "candidate_urls": candidate_urls,
                    "path": path,
                    "has_signature_header": signature is not None,
                    "form_param_keys": list(params.keys()),
                    "blank_form_param_keys": blank_keys,
                    "forwarded_proto": headers.get("x-forwarded-proto"),
                    "forwarded_host": headers.get("x-forwarded-host"),
                    "host": headers.get("host"),
                    "hint": (
                        "Check PUBLIC_BASE_URL matches ngrok URL exactly, "
                        "and verify TWILIO_AUTH_TOKEN."
                    ),
                },
            )

            response_body = b"Invalid Twilio signature."

            await send({
                "type": "http.response.start",
                "status": 403,
                "headers": [
                    (b"content-type", b"text/plain"),
                    (b"content-length", str(len(response_body)).encode("latin-1")),
                ],
            })

            await send({
                "type": "http.response.body",
                "body": response_body,
            })

            return

        already_sent = False

        async def replay_receive() -> Message:
            nonlocal already_sent

            if already_sent:
                return {
                    "type": "http.request",
                    "body": b"",
                    "more_body": False,
                }

            already_sent = True

            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }

        await self.app(scope, replay_receive, send)
