from urllib.parse import parse_qs

from starlette.types import ASGIApp, Message, Receive, Scope, Send
from twilio.request_validator import RequestValidator

from app.config import settings


def _is_twilio_path(path: str) -> bool:
    return path == "/twilio" or path.startswith("/twilio/")


def _build_public_url(scope: Scope) -> str:
    """
    Twilio signs the public URL it called, not your localhost URL.

    Since we are behind ngrok locally, we rebuild the URL using
    PUBLIC_BASE_URL from .env plus the request path/query.
    """

    path = scope.get("path", "")
    query_string = scope.get("query_string", b"").decode("utf-8")

    url = f"{settings.public_base_url.rstrip('/')}{path}"

    if query_string:
        url = f"{url}?{query_string}"

    return url


def _parse_form_params(body: bytes) -> dict[str, str]:
    parsed = parse_qs(body.decode("utf-8"))

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

        public_url = _build_public_url(scope)
        params = _parse_form_params(body)

        is_valid = self.validator.validate(
            public_url,
            params,
            signature or "",
        )

        if not is_valid:
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

            print("\nInvalid Twilio signature")
            print("------------------------")
            print(f"Validated URL: {public_url}")
            print(f"Path: {path}")
            print("Check PUBLIC_BASE_URL and ngrok URL.")

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