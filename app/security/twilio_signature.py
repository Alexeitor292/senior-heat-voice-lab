from urllib.parse import parse_qs, parse_qsl, urlparse

from starlette.types import ASGIApp, Message, Receive, Scope, Send
from twilio.request_validator import RequestValidator

from app.config import settings
from app.utils.safe_logging import safe_log_event


def _is_twilio_path(path: str) -> bool:
    return path == "/twilio" or path.startswith("/twilio/")


def _build_validated_url(scope: Scope) -> str:
    """
    Reconstructs the exact URL Twilio signed.

    Twilio signs the public URL it called, so we use PUBLIC_BASE_URL
    from config — never raw forwarded headers, which are attacker-controlled.
    """
    path = scope.get("path", "")
    query_string = scope.get("query_string", b"").decode("utf-8")
    suffix = path + (f"?{query_string}" if query_string else "")
    return f"{settings.public_base_url.rstrip('/')}{suffix}"


def _parse_form_params(body: bytes) -> dict[str, str]:
    """
    Parses a Twilio form body preserving blank values.

    Uses parse_qs with first-value semantics (values[0]) to match how
    Twilio's RequestValidator hashes params — Twilio never sends duplicate
    keys, but if it did, first-value-wins is the safe default.
    """
    parsed = parse_qs(
        body.decode("utf-8"),
        keep_blank_values=True,
    )
    return {
        key: values[0] if values else ""
        for key, values in parsed.items()
    }


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
        validated_url = _build_validated_url(scope)

        is_valid = self.validator.validate(validated_url, params, signature or "")

        if not is_valid:
            query_string = scope.get("query_string", b"").decode("utf-8")
            blank_keys = [k for k, v in params.items() if v == ""]
            query_param_names = [k for k, _ in parse_qsl(query_string)]
            parsed_base = urlparse(settings.public_base_url)
            public_base_origin = f"{parsed_base.scheme}://{parsed_base.netloc}"

            safe_log_event(
                "Invalid Twilio Signature",
                {
                    "path": path,
                    "public_base_url_origin": public_base_origin,
                    "has_signature_header": signature is not None,
                    "query_param_names": query_param_names,
                    "form_param_keys": list(params.keys()),
                    "blank_form_param_keys": blank_keys,
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
