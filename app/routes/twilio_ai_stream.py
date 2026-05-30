from __future__ import annotations

import json
from urllib.parse import urlparse
from xml.sax.saxutils import escape, quoteattr

from fastapi import APIRouter, Query, Response, WebSocket, WebSocketDisconnect

from app.config import settings
from app.db.database import SessionLocal
from app.db.models import CheckInCallSession
from app.schemas.ai_call_sessions import AICallSessionStartRequest
from app.services.ai_call_session_adapter_service import ai_call_session_adapter_service
from app.utils.safe_logging import safe_log_event


router = APIRouter(prefix="/twilio", tags=["Twilio AI Stream"])


def _public_ws_url(path: str) -> str:
    """
    Convert PUBLIC_BASE_URL into a websocket URL Twilio can connect to.

    Example:
    https://abc.ngrok-free.app -> wss://abc.ngrok-free.app/twilio/media/ai-check-in
    http://localhost:8000  -> ws://localhost:8000/twilio/media/ai-check-in
    """
    parsed = urlparse(settings.public_base_url.rstrip("/"))

    if parsed.scheme == "https":
        ws_scheme = "wss"
    elif parsed.scheme == "http":
        ws_scheme = "ws"
    else:
        ws_scheme = "wss"

    return f"{ws_scheme}://{parsed.netloc}{path}"


def _ai_stream_twiml(
    *,
    senior_id: int,
    stream_url: str,
) -> str:
    # Generate TwiML manually so we do not depend on Twilio SDK helper behavior
    # for custom <Parameter> elements.
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Hello. This is your AI wellness companion check-in. One moment while I connect you.</Say>
  <Connect>
    <Stream url={quoteattr(stream_url)}>
      <Parameter name="senior_id" value={quoteattr(str(senior_id))} />
      <Parameter name="provider" value="twilio_media_stream" />
    </Stream>
  </Connect>
</Response>
"""


def _update_call_session_status(
    *,
    session_id: int,
    status: str,
    duration_seconds: int | None = None,
) -> None:
    with SessionLocal() as db:
        session = db.get(CheckInCallSession, session_id)

        if not session:
            return

        session.status = status

        if duration_seconds is not None:
            session.duration_seconds = duration_seconds

        db.commit()


@router.post("/voice/ai-check-in")
async def ai_check_in_voice(
    senior_id: int = Query(...),
):
    """
    Twilio voice webhook for the real AI check-in path.

    This returns TwiML that connects the phone call to our backend WebSocket.
    The WebSocket is where Pipecat/OpenAI Realtime will plug in next.
    """
    stream_url = _public_ws_url("/twilio/media/ai-check-in")

    safe_log_event(
        "AI Check-In TwiML Generated",
        {
            "senior_id": senior_id,
            "stream_url": stream_url,
        },
    )

    return Response(
        content=_ai_stream_twiml(
            senior_id=senior_id,
            stream_url=stream_url,
        ),
        media_type="application/xml",
    )


@router.websocket("/media/ai-check-in")
async def ai_check_in_media_stream(websocket: WebSocket):
    """
    Twilio Media Stream WebSocket endpoint.

    Current milestone:
    - Accept Twilio's bidirectional stream.
    - Create our AI call session when Twilio sends the start event.
    - Track media events so we know audio is reaching the backend.
    - Mark the session ended when Twilio sends stop/disconnect.

    Next milestone:
    - Pipe inbound audio frames into Pipecat/OpenAI Realtime.
    - Send generated audio frames back to Twilio.
    - Append transcript turns live.
    - Complete/analyze the session at call end.
    """
    await websocket.accept()

    session_id: int | None = None
    senior_id: int | None = None
    call_sid: str | None = None
    stream_sid: str | None = None
    media_event_count = 0

    safe_log_event(
        "AI Media Stream Connected",
        {
            "client": str(websocket.client),
        },
    )

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                safe_log_event(
                    "AI Media Stream Invalid JSON",
                    {
                        "message_preview": raw_message[:120],
                    },
                )
                continue

            event = message.get("event")

            if event == "connected":
                safe_log_event(
                    "AI Media Stream Twilio Connected Event",
                    {
                        "protocol": message.get("protocol"),
                        "version": message.get("version"),
                    },
                )

            elif event == "start":
                start = message.get("start") or {}
                custom_parameters = start.get("customParameters") or {}

                stream_sid = start.get("streamSid") or message.get("streamSid")
                call_sid = start.get("callSid")
                senior_id_raw = custom_parameters.get("senior_id")

                try:
                    senior_id = int(senior_id_raw)
                except (TypeError, ValueError):
                    senior_id = None

                if senior_id is None:
                    safe_log_event(
                        "AI Media Stream Missing Senior ID",
                        {
                            "call_sid": call_sid,
                            "stream_sid": stream_sid,
                            "custom_parameters": custom_parameters,
                        },
                    )
                    await websocket.close(code=1008)
                    return

                result = ai_call_session_adapter_service.start_session(
                    senior_id=senior_id,
                    payload=AICallSessionStartRequest(
                        provider="twilio_media_stream",
                        provider_session_id=stream_sid,
                        senior_call_sid=call_sid,
                        call_status="in_progress",
                        raw_provider_payload={
                            "stream_sid": stream_sid,
                            "custom_parameters": custom_parameters,
                            "start_event": start,
                        },
                    ),
                )

                if not result:
                    safe_log_event(
                        "AI Media Stream Senior Not Found",
                        {
                            "senior_id": senior_id,
                            "call_sid": call_sid,
                            "stream_sid": stream_sid,
                        },
                    )
                    await websocket.close(code=1008)
                    return

                session_id = result["session"]["id"]

                safe_log_event(
                    "AI Media Stream Session Started",
                    {
                        "session_id": session_id,
                        "senior_id": senior_id,
                        "call_sid": call_sid,
                        "stream_sid": stream_sid,
                    },
                )

            elif event == "media":
                media_event_count += 1

                # Do not log payloads. They contain raw audio.
                if media_event_count in {1, 10, 50, 100}:
                    safe_log_event(
                        "AI Media Stream Audio Received",
                        {
                            "session_id": session_id,
                            "senior_id": senior_id,
                            "call_sid": call_sid,
                            "stream_sid": stream_sid,
                            "media_event_count": media_event_count,
                        },
                    )

            elif event == "mark":
                safe_log_event(
                    "AI Media Stream Mark Event",
                    {
                        "session_id": session_id,
                        "mark": message.get("mark"),
                    },
                )

            elif event == "stop":
                stop = message.get("stop") or {}

                safe_log_event(
                    "AI Media Stream Stop Event",
                    {
                        "session_id": session_id,
                        "senior_id": senior_id,
                        "call_sid": call_sid,
                        "stream_sid": stream_sid,
                        "media_event_count": media_event_count,
                        "stop_event": stop,
                    },
                )

                if session_id is not None:
                    _update_call_session_status(
                        session_id=session_id,
                        status="stream_stopped_no_analysis",
                    )

                break

            else:
                safe_log_event(
                    "AI Media Stream Unhandled Event",
                    {
                        "event": event,
                        "session_id": session_id,
                    },
                )

    except WebSocketDisconnect:
        safe_log_event(
            "AI Media Stream Disconnected",
            {
                "session_id": session_id,
                "senior_id": senior_id,
                "call_sid": call_sid,
                "stream_sid": stream_sid,
                "media_event_count": media_event_count,
            },
        )

        if session_id is not None:
            _update_call_session_status(
                session_id=session_id,
                status="stream_disconnected_no_analysis",
            )