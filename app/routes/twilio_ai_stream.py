from __future__ import annotations

import json
import time
from urllib.parse import urlparse
from xml.sax.saxutils import quoteattr

from fastapi import APIRouter, Query, Response, WebSocket, WebSocketDisconnect

from app.config import settings
from app.db.database import SessionLocal
from app.db.models import CheckInCallSession
from app.schemas.ai_call_sessions import (
    AICallSessionCompleteRequest,
    AICallSessionStartRequest,
)
from app.services.ai_call_session_adapter_service import ai_call_session_adapter_service
from app.services.openai_realtime_twilio_bridge import OpenAIRealtimeTwilioBridge
from app.utils.safe_logging import safe_log_event


router = APIRouter(prefix="/twilio", tags=["Twilio AI Stream"])


def _public_ws_url(path: str) -> str:
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
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
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


def _get_session_senior_name(session_id: int) -> str | None:
    with SessionLocal() as db:
        session = db.get(CheckInCallSession, session_id)

        if not session:
            return None

        return session.senior_name


def _complete_stream_session(
    *,
    session_id: int,
    call_sid: str | None,
    stream_sid: str | None,
    media_event_count: int,
    duration_seconds: int | None,
    terminal_reason: str | None = None,
) -> None:
    result = ai_call_session_adapter_service.complete_existing_session(
        session_id=session_id,
        payload=AICallSessionCompleteRequest(
            provider="twilio_openai_realtime",
            provider_session_id=stream_sid,
            senior_call_sid=call_sid,
            call_status="completed",
            duration_seconds=duration_seconds,
            create_operator_actions=True,
            raw_provider_payload={
                "stream_sid": stream_sid,
                "media_event_count": media_event_count,
                "duration_seconds": duration_seconds,
                "terminal_reason": terminal_reason,
            },
        ),
    )

    if result:
        safe_log_event(
            "AI Media Stream Completed And Analyzed",
            {
                "session_id": session_id,
                "check_in_id": result.get("check_in_id"),
                "insight_id": result.get("insight_id"),
                "review_url": result.get("check_in_review_url"),
                "terminal_reason": terminal_reason,
            },
        )
        return

    status = (
        "idle_timeout_no_transcript"
        if terminal_reason == "idle_timeout"
        else "stream_stopped_no_transcript"
    )

    _update_call_session_status(
        session_id=session_id,
        status=status,
        duration_seconds=duration_seconds,
    )

    safe_log_event(
        "AI Media Stream Stopped Without Senior Transcript",
        {
            "session_id": session_id,
            "call_sid": call_sid,
            "stream_sid": stream_sid,
            "status": status,
            "duration_seconds": duration_seconds,
            "terminal_reason": terminal_reason,
        },
    )


@router.post("/voice/ai-check-in")
async def ai_check_in_voice(
    senior_id: int = Query(...),
):
    stream_url = _public_ws_url("/twilio/media/ai-check-in")

    safe_log_event(
        "AI Check-In TwiML Generated",
        {
            "senior_id": senior_id,
            "stream_url": stream_url,
            "openai_realtime_enabled": settings.openai_realtime_enabled,
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
    await websocket.accept()

    session_id: int | None = None
    senior_id: int | None = None
    call_sid: str | None = None
    stream_sid: str | None = None
    media_event_count = 0
    stream_started_at_monotonic: float | None = None
    realtime_bridge: OpenAIRealtimeTwilioBridge | None = None

    safe_log_event(
        "AI Media Stream Connected",
        {
            "client": str(websocket.client),
            "openai_realtime_enabled": settings.openai_realtime_enabled,
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
                stream_started_at_monotonic = time.monotonic()

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
                senior_name = _get_session_senior_name(session_id)

                safe_log_event(
                    "AI Media Stream Session Started",
                    {
                        "session_id": session_id,
                        "senior_id": senior_id,
                        "call_sid": call_sid,
                        "stream_sid": stream_sid,
                        "reused_existing_session": result.get("reused_existing_session"),
                    },
                )

                if stream_sid:
                    realtime_bridge = OpenAIRealtimeTwilioBridge(
                        twilio_websocket=websocket,
                        session_id=session_id,
                        senior_id=senior_id,
                        stream_sid=stream_sid,
                        call_sid=call_sid,
                        senior_name=senior_name,
                    )
                    await realtime_bridge.start()

            elif event == "media":
                media_event_count += 1

                media = message.get("media") or {}
                payload = media.get("payload")

                if realtime_bridge:
                    await realtime_bridge.send_twilio_audio_payload(payload)

                if media_event_count in {1, 10, 50, 100}:
                    safe_log_event(
                        "AI Media Stream Audio Received",
                        {
                            "session_id": session_id,
                            "senior_id": senior_id,
                            "call_sid": call_sid,
                            "stream_sid": stream_sid,
                            "media_event_count": media_event_count,
                            "forwarding_to_openai": realtime_bridge is not None,
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

                if realtime_bridge and realtime_bridge.should_end_after_twilio_mark():
                    await realtime_bridge.complete_twilio_call(
                        "senior_farewell_after_assistant_audio"
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

                if realtime_bridge:
                    await realtime_bridge.close()

                if session_id is not None:
                    duration_seconds = None

                    if stream_started_at_monotonic is not None:
                        duration_seconds = max(0, int(time.monotonic() - stream_started_at_monotonic))
                    _complete_stream_session(
                        session_id=session_id,
                        call_sid=call_sid,
                        stream_sid=stream_sid,
                        media_event_count=media_event_count,
                        duration_seconds=duration_seconds,
                        terminal_reason=realtime_bridge.call_end_reason if realtime_bridge else None,
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

        if realtime_bridge:
            await realtime_bridge.close()

        if session_id is not None:
            duration_seconds = None

            if stream_started_at_monotonic is not None:
                duration_seconds = max(0, int(time.monotonic() - stream_started_at_monotonic))
            _update_call_session_status(
                session_id=session_id,
                status="stream_disconnected",
                duration_seconds=duration_seconds,
            )