from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
from collections import defaultdict
from typing import Any

import websockets
from fastapi import WebSocket
from websockets.exceptions import ConnectionClosed

from app.config import settings
from app.schemas.ai_call_sessions import AICallSessionTurnRequest
from app.services.ai_call_session_adapter_service import ai_call_session_adapter_service
from app.services.twilio_service import twilio_service
from app.utils.safe_logging import safe_log_event


REALTIME_URL_TEMPLATE = "wss://api.openai.com/v1/realtime?model={model}"

IDLE_CHECK_SECONDS = 25
IDLE_FINAL_SECONDS = 20
HOLD_SECONDS = 90


FAREWELL_PATTERNS = [
    r"\bbye\b",
    r"\bbye[-\s]?bye\b",
    r"\bgoodbye\b",
    r"\btalk to you later\b",
    r"\bsee you\b",
    r"\bthat'?s all\b",
    r"\bthat is all\b",
    r"\bi'?m done\b",
    r"\bi am done\b",
    r"\bnothing else\b",
    r"\bno thank you\b",
    r"\bno thanks\b",
]

HOLD_REQUEST_PATTERNS = [
    r"\bhold on\b",
    r"\bhold up\b",
    r"\bwait\b",
    r"\bwait a second\b",
    r"\bwait a minute\b",
    r"\bgive me a second\b",
    r"\bgive me a minute\b",
    r"\bone second\b",
    r"\bone minute\b",
    r"\bjust a second\b",
    r"\bjust a minute\b",
    r"\bjust a sec\b",
    r"\bi'?ll be right back\b",
    r"\bi will be right back\b",
    r"\bbe right back\b",
    r"\bbrb\b",
]


def _stable_safety_identifier(senior_id: int) -> str:
    raw = f"senior-heat-voice-lab:senior:{senior_id}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _extract_text(event: dict[str, Any]) -> str | None:
    for key in ("transcript", "text", "delta"):
        value = event.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _looks_like_farewell(text: str) -> bool:
    normalized = text.lower().strip()

    if not normalized:
        return False

    return any(re.search(pattern, normalized) for pattern in FAREWELL_PATTERNS)


def _looks_like_hold_request(text: str) -> bool:
    normalized = text.lower().strip()

    if not normalized:
        return False

    return any(re.search(pattern, normalized) for pattern in HOLD_REQUEST_PATTERNS)


class OpenAIRealtimeTwilioBridge:
    def __init__(
        self,
        *,
        twilio_websocket: WebSocket,
        session_id: int,
        senior_id: int,
        stream_sid: str,
        call_sid: str | None = None,
        senior_name: str | None = None,
    ):
        self.twilio_websocket = twilio_websocket
        self.session_id = session_id
        self.senior_id = senior_id
        self.stream_sid = stream_sid
        self.call_sid = call_sid
        self.senior_name = senior_name or "the senior"

        self.openai_ws = None
        self.openai_receive_task: asyncio.Task | None = None
        self.idle_watch_task: asyncio.Task | None = None

        self.assistant_transcript_buffers: dict[str, list[str]] = defaultdict(list)
        self.output_audio_chunks_sent = 0
        self.user_turns_captured = 0
        self.assistant_turns_captured = 0

        now = time.monotonic()
        self.last_senior_activity_monotonic = now
        self.last_assistant_audio_done_monotonic = now

        self.idle_check_sent = False
        self.idle_check_sent_monotonic: float | None = None
        self.hold_until_monotonic: float | None = None

        self.senior_requested_call_end = False
        self.pending_call_end_after_audio = False
        self.call_end_requested = False
        self.call_end_reason: str | None = None

    async def start(self) -> bool:
        if not settings.openai_realtime_enabled:
            safe_log_event(
                "OpenAI Realtime Bridge Disabled",
                {
                    "session_id": self.session_id,
                    "senior_id": self.senior_id,
                },
            )
            return False

        api_key = (settings.openai_api_key or "").strip()

        if not api_key:
            safe_log_event(
                "OpenAI Realtime Bridge Missing API Key",
                {
                    "session_id": self.session_id,
                    "senior_id": self.senior_id,
                },
            )
            return False

        url = REALTIME_URL_TEMPLATE.format(model=settings.openai_realtime_model)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Safety-Identifier": _stable_safety_identifier(self.senior_id),
        }

        try:
            safe_log_event(
                "OpenAI Realtime Bridge Connecting",
                {
                    "session_id": self.session_id,
                    "senior_id": self.senior_id,
                    "model": settings.openai_realtime_model,
                    "voice": settings.openai_realtime_voice,
                    "api_key_prefix": api_key[:8],
                    "api_key_length": len(api_key),
                },
            )

            try:
                self.openai_ws = await websockets.connect(
                    url,
                    additional_headers=headers,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=None,
                )
            except TypeError:
                # Older websockets versions use extra_headers.
                self.openai_ws = await websockets.connect(
                    url,
                    extra_headers=headers,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=None,
                )

            await self._configure_session()
            self.openai_receive_task = asyncio.create_task(self._receive_openai_events())
            self.idle_watch_task = asyncio.create_task(self._watch_for_idle_call())
            await self._start_greeting()

            safe_log_event(
                "OpenAI Realtime Bridge Started",
                {
                    "session_id": self.session_id,
                    "senior_id": self.senior_id,
                    "model": settings.openai_realtime_model,
                    "voice": settings.openai_realtime_voice,
                },
            )
            return True

        except Exception as exc:
            safe_log_event(
                "OpenAI Realtime Bridge Start Failed",
                {
                    "session_id": self.session_id,
                    "senior_id": self.senior_id,
                    "error": repr(exc),
                },
            )
            await self.close()
            return False

    async def send_twilio_audio_payload(self, payload: str | None) -> None:
        if not payload or self.openai_ws is None:
            return

        try:
            await self._send_openai(
                {
                    "type": "input_audio_buffer.append",
                    "audio": payload,
                }
            )
        except Exception as exc:
            safe_log_event(
                "OpenAI Realtime Audio Forward Failed",
                {
                    "session_id": self.session_id,
                    "error": repr(exc),
                },
            )

    async def close(self) -> None:
        if self.idle_watch_task:
            self.idle_watch_task.cancel()

            try:
                await self.idle_watch_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

            self.idle_watch_task = None

        if self.openai_receive_task:
            self.openai_receive_task.cancel()

            try:
                await self.openai_receive_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

            self.openai_receive_task = None

        if self.openai_ws:
            try:
                await self.openai_ws.close()
            except Exception:
                pass

            self.openai_ws = None

    async def _configure_session(self) -> None:
        instructions = (
            "You are a warm, patient AI wellness companion calling an older adult for a "
            "brief heat safety and wellbeing check-in. Sound natural, calm, and human. "
            "Do not sound like a survey or a medical form. Ask one short question at a time. "
            "Keep most replies to one or two short sentences. "
            "First ask how they are feeling. Then naturally ask whether the home feels too hot, "
            "whether they have had water, and whether someone nearby can check on them if needed. "
            "If they report mild symptoms like feeling a little dizzy, tired, warm, or thirsty, "
            "acknowledge it gently and suggest simple safety steps like sitting somewhere cooler, "
            "sipping water, and contacting a trusted person nearby. "
            "Only mention emergency services when the senior reports severe symptoms or direct danger, "
            "such as chest pain, trouble breathing, fainting, severe confusion, a fall, or asking for emergency help. "
            "Do not repeat the same emergency warning in every turn. "
            "If the senior says goodbye, bye-bye, that is all, or otherwise clearly ends the conversation, "
            "give one short warm goodbye and do not ask another question. "
            "If the senior asks you to wait, hold on, or says they will be right back, "
            "acknowledge briefly and wait quietly. Do not keep asking questions during a short hold. "
            "Do not diagnose medical conditions."
        )

        await self._send_openai(
            {
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "instructions": instructions,
                    "output_modalities": ["audio"],
                    "audio": {
                        "input": {
                            "format": {
                                "type": "audio/pcmu",
                            },
                            "turn_detection": {
                                "type": "server_vad",
                                "threshold": 0.5,
                                "prefix_padding_ms": 300,
                                "silence_duration_ms": 700,
                                "create_response": True,
                            },
                            "transcription": {
                                "model": "gpt-4o-mini-transcribe",
                            },
                        },
                        "output": {
                            "format": {
                                "type": "audio/pcmu",
                            },
                            "voice": settings.openai_realtime_voice,
                        },
                    },
                },
            }
        )

    async def _start_greeting(self) -> None:
        await self._create_assistant_response(
            f"Greet {self.senior_name} warmly and directly. "
            "Say you are calling for a quick wellness and heat safety check-in. "
            "Then ask how they are feeling today. Keep it short."
        )

    async def _send_openai(self, event: dict[str, Any]) -> None:
        if self.openai_ws is None:
            return

        await self.openai_ws.send(json.dumps(event))

    async def _create_assistant_response(self, instructions: str) -> None:
        await self._send_openai(
            {
                "type": "response.create",
                "response": {
                    "output_modalities": ["audio"],
                    "instructions": instructions,
                },
            }
        )

    async def _receive_openai_events(self) -> None:
        if self.openai_ws is None:
            return

        try:
            async for raw_message in self.openai_ws:
                if isinstance(raw_message, bytes):
                    raw_message = raw_message.decode("utf-8", errors="replace")

                try:
                    event = json.loads(raw_message)
                except json.JSONDecodeError:
                    safe_log_event(
                        "OpenAI Realtime Invalid JSON",
                        {
                            "session_id": self.session_id,
                            "message_preview": str(raw_message)[:120],
                        },
                    )
                    continue

                await self._handle_openai_event(event)

        except asyncio.CancelledError:
            raise
        except ConnectionClosed:
            safe_log_event(
                "OpenAI Realtime Connection Closed",
                {
                    "session_id": self.session_id,
                },
            )
        except Exception as exc:
            safe_log_event(
                "OpenAI Realtime Receive Loop Failed",
                {
                    "session_id": self.session_id,
                    "error": repr(exc),
                },
            )

    def _record_senior_activity(self) -> None:
        self.last_senior_activity_monotonic = time.monotonic()
        self.idle_check_sent = False
        self.idle_check_sent_monotonic = None

        if self.hold_until_monotonic is not None:
            self.hold_until_monotonic = None

        if self.call_end_reason == "idle_timeout" and not self.call_end_requested:
            self.senior_requested_call_end = False
            self.pending_call_end_after_audio = False
            self.call_end_reason = None

    def _record_assistant_audio_done(self) -> None:
        self.last_assistant_audio_done_monotonic = time.monotonic()

    async def _watch_for_idle_call(self) -> None:
        try:
            while True:
                await asyncio.sleep(1)

                if self.call_end_requested:
                    return

                now = time.monotonic()

                if self.hold_until_monotonic is not None:
                    if now < self.hold_until_monotonic:
                        continue

                    self.hold_until_monotonic = None

                    safe_log_event(
                        "AI Media Stream Hold Window Expired",
                        {
                            "session_id": self.session_id,
                            "call_sid": self.call_sid,
                        },
                    )

                last_activity = max(
                    self.last_senior_activity_monotonic,
                    self.last_assistant_audio_done_monotonic,
                )
                idle_for = now - last_activity

                if not self.idle_check_sent and idle_for >= IDLE_CHECK_SECONDS:
                    self.idle_check_sent = True
                    self.idle_check_sent_monotonic = now

                    safe_log_event(
                        "AI Media Stream Idle Check Prompt",
                        {
                            "session_id": self.session_id,
                            "call_sid": self.call_sid,
                            "idle_for_seconds": int(idle_for),
                        },
                    )

                    await self._create_assistant_response(
                        "The senior has been quiet. Gently ask: 'Are you still there?' "
                        "Keep it warm, short, and do not end the call yet."
                    )

                    continue

                if (
                    self.idle_check_sent
                    and self.idle_check_sent_monotonic is not None
                    and now - self.idle_check_sent_monotonic >= IDLE_FINAL_SECONDS
                ):
                    self.senior_requested_call_end = True
                    self.call_end_reason = "idle_timeout"

                    safe_log_event(
                        "AI Media Stream Idle Timeout Final Goodbye",
                        {
                            "session_id": self.session_id,
                            "call_sid": self.call_sid,
                        },
                    )

                    await self._create_assistant_response(
                        "The senior did not respond after a gentle check. "
                        "Say one short warm goodbye, such as: "
                        "'I’ll end the call for now. Please take care and stay cool.' "
                        "Do not ask another question."
                    )

                    return

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            safe_log_event(
                "AI Media Stream Idle Watch Failed",
                {
                    "session_id": self.session_id,
                    "call_sid": self.call_sid,
                    "error": repr(exc),
                },
            )

    async def _handle_openai_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type")

        if event_type == "error":
            safe_log_event(
                "OpenAI Realtime Error",
                {
                    "session_id": self.session_id,
                    "error": event.get("error"),
                },
            )
            return

        if event_type in {"response.output_audio.delta", "response.audio.delta"}:
            audio_delta = event.get("delta")

            if isinstance(audio_delta, str) and audio_delta:
                await self._send_twilio_audio(audio_delta)

            return

        if event_type in {"response.output_audio.done", "response.audio.done"}:
            self._record_assistant_audio_done()

            if self.senior_requested_call_end:
                self.pending_call_end_after_audio = True

                safe_log_event(
                    "AI Media Stream Queued Call End After Audio",
                    {
                        "session_id": self.session_id,
                        "call_sid": self.call_sid,
                        "reason": self.call_end_reason,
                    },
                )

            await self._send_twilio_mark()
            return

        if event_type in {
            "conversation.item.input_audio_transcription.completed",
            "conversation.item.input_audio_transcription.done",
            "input_audio_transcription.completed",
        }:
            transcript = _extract_text(event)

            if transcript:
                self._record_senior_activity()

                self.user_turns_captured += 1
                ai_call_session_adapter_service.append_turn(
                    session_id=self.session_id,
                    payload=AICallSessionTurnRequest(
                        speaker="senior",
                        text=transcript,
                    ),
                )

                if _looks_like_farewell(transcript):
                    self.senior_requested_call_end = True
                    self.call_end_reason = "senior_farewell"

                    safe_log_event(
                        "AI Media Stream Senior Farewell Detected",
                        {
                            "session_id": self.session_id,
                            "turns": self.user_turns_captured,
                        },
                    )

                if _looks_like_hold_request(transcript):
                    self.hold_until_monotonic = time.monotonic() + HOLD_SECONDS
                    self.idle_check_sent = False
                    self.idle_check_sent_monotonic = None

                    safe_log_event(
                        "AI Media Stream Senior Hold Requested",
                        {
                            "session_id": self.session_id,
                            "hold_seconds": HOLD_SECONDS,
                        },
                    )

                safe_log_event(
                    "OpenAI Realtime Senior Transcript Captured",
                    {
                        "session_id": self.session_id,
                        "turns": self.user_turns_captured,
                    },
                )

            return

        if event_type in {
            "response.output_audio_transcript.delta",
            "response.audio_transcript.delta",
            "response.output_text.delta",
        }:
            delta = _extract_text(event)

            if delta:
                key = (
                    event.get("item_id")
                    or event.get("response_id")
                    or event.get("output_index")
                    or "assistant"
                )
                self.assistant_transcript_buffers[str(key)].append(delta)

            return

        if event_type in {
            "response.output_audio_transcript.done",
            "response.audio_transcript.done",
            "response.output_text.done",
        }:
            key = (
                event.get("item_id")
                or event.get("response_id")
                or event.get("output_index")
                or "assistant"
            )

            transcript = event.get("transcript") or event.get("text")

            if not transcript:
                transcript = "".join(
                    self.assistant_transcript_buffers.pop(str(key), [])
                )

            transcript = transcript.strip() if isinstance(transcript, str) else ""

            if transcript:
                self.assistant_turns_captured += 1
                ai_call_session_adapter_service.append_turn(
                    session_id=self.session_id,
                    payload=AICallSessionTurnRequest(
                        speaker="assistant",
                        text=transcript,
                    ),
                )

                safe_log_event(
                    "OpenAI Realtime Assistant Transcript Captured",
                    {
                        "session_id": self.session_id,
                        "turns": self.assistant_turns_captured,
                    },
                )

            return

        if event_type == "input_audio_buffer.speech_started":
            # Interrupt buffered assistant audio when the senior starts talking.
            await self._send_twilio_clear()
            return

        if event_type == "response.done":
            if self.senior_requested_call_end:
                self.pending_call_end_after_audio = True

            safe_log_event(
                "OpenAI Realtime Event",
                {
                    "session_id": self.session_id,
                    "event_type": event_type,
                    "pending_call_end_after_audio": self.pending_call_end_after_audio,
                    "reason": self.call_end_reason,
                },
            )
            return

        if event_type in {
            "session.created",
            "session.updated",
            "response.created",
            "input_audio_buffer.speech_stopped",
        }:
            safe_log_event(
                "OpenAI Realtime Event",
                {
                    "session_id": self.session_id,
                    "event_type": event_type,
                },
            )
            return

    def should_end_after_twilio_mark(self) -> bool:
        return self.pending_call_end_after_audio and not self.call_end_requested

    async def complete_twilio_call(self, reason: str) -> None:
        if self.call_end_requested:
            return

        if not self.call_sid:
            safe_log_event(
                "AI Media Stream Call End Skipped",
                {
                    "session_id": self.session_id,
                    "reason": reason,
                    "message": "Missing Twilio call SID.",
                },
            )
            return

        self.call_end_requested = True

        safe_log_event(
            "AI Media Stream Ending Twilio Call",
            {
                "session_id": self.session_id,
                "call_sid": self.call_sid,
                "reason": reason,
            },
        )

        try:
            await asyncio.to_thread(twilio_service.complete_call, self.call_sid)
        except Exception as exc:
            safe_log_event(
                "AI Media Stream End Twilio Call Failed",
                {
                    "session_id": self.session_id,
                    "call_sid": self.call_sid,
                    "reason": reason,
                    "error": repr(exc),
                },
            )

    async def _send_twilio_audio(self, payload: str) -> None:
        await self.twilio_websocket.send_text(
            json.dumps(
                {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {
                        "payload": payload,
                    },
                }
            )
        )

        self.output_audio_chunks_sent += 1

        if self.output_audio_chunks_sent in {1, 10, 50, 100}:
            safe_log_event(
                "OpenAI Realtime Audio Sent To Twilio",
                {
                    "session_id": self.session_id,
                    "chunks": self.output_audio_chunks_sent,
                },
            )

    async def _send_twilio_mark(self) -> None:
        await self.twilio_websocket.send_text(
            json.dumps(
                {
                    "event": "mark",
                    "streamSid": self.stream_sid,
                    "mark": {
                        "name": f"assistant-response-{self.output_audio_chunks_sent}",
                    },
                }
            )
        )

    async def _send_twilio_clear(self) -> None:
        await self.twilio_websocket.send_text(
            json.dumps(
                {
                    "event": "clear",
                    "streamSid": self.stream_sid,
                }
            )
        )