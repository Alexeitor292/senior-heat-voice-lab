from __future__ import annotations

import asyncio
import hashlib
import json
from collections import defaultdict
from typing import Any

import websockets
from fastapi import WebSocket
from websockets.exceptions import ConnectionClosed

from app.config import settings
from app.schemas.ai_call_sessions import AICallSessionTurnRequest
from app.services.ai_call_session_adapter_service import ai_call_session_adapter_service
from app.utils.safe_logging import safe_log_event


REALTIME_URL_TEMPLATE = "wss://api.openai.com/v1/realtime?model={model}"


def _stable_safety_identifier(senior_id: int) -> str:
    raw = f"senior-heat-voice-lab:senior:{senior_id}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _extract_text(event: dict[str, Any]) -> str | None:
    for key in ("transcript", "text", "delta"):
        value = event.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


class OpenAIRealtimeTwilioBridge:
    def __init__(
        self,
        *,
        twilio_websocket: WebSocket,
        session_id: int,
        senior_id: int,
        stream_sid: str,
        senior_name: str | None = None,
    ):
        self.twilio_websocket = twilio_websocket
        self.session_id = session_id
        self.senior_id = senior_id
        self.stream_sid = stream_sid
        self.senior_name = senior_name or "the senior"

        self.openai_ws = None
        self.openai_receive_task: asyncio.Task | None = None
        self.assistant_transcript_buffers: dict[str, list[str]] = defaultdict(list)
        self.output_audio_chunks_sent = 0
        self.user_turns_captured = 0
        self.assistant_turns_captured = 0

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
            "You are a warm, patient AI wellness companion calling an older adult. "
            "Your job is to have a natural check-in conversation, not a survey. "
            "Be brief, gentle, and conversational. Ask about how they are feeling, "
            "whether their home feels too hot, whether they have had water, and whether "
            "someone they trust can check on them if needed. If they report urgent danger "
            "such as chest pain, trouble breathing, fainting, confusion, a fall, or asking "
            "for emergency help, calmly tell them you will make sure a human is notified. "
            "Do not give a medical diagnosis. Keep responses short because this is a phone call."
        )

        # GA-style shape. If OpenAI returns a schema error, paste the error back
        # and we will adjust this object to the exact model/session version.
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
        await self._send_openai(
            {
                "type": "response.create",
                "response": {
                    "output_modalities": ["audio"],
                    "instructions": (
                        f"Start the call by greeting {self.senior_name}. "
                        "Say you are calling for a quick wellness and heat safety check-in. "
                        "Then ask how they are feeling today."
                    ),
                },
            }
        )

    async def _send_openai(self, event: dict[str, Any]) -> None:
        if self.openai_ws is None:
            return

        await self.openai_ws.send(json.dumps(event))

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
            await self._send_twilio_mark()
            return

        if event_type in {
            "conversation.item.input_audio_transcription.completed",
            "conversation.item.input_audio_transcription.done",
            "input_audio_transcription.completed",
        }:
            transcript = _extract_text(event)

            if transcript:
                self.user_turns_captured += 1
                ai_call_session_adapter_service.append_turn(
                    session_id=self.session_id,
                    payload=AICallSessionTurnRequest(
                        speaker="senior",
                        text=transcript,
                    ),
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
                transcript = "".join(self.assistant_transcript_buffers.pop(str(key), []))

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

        if event_type in {
            "session.created",
            "session.updated",
            "response.created",
            "response.done",
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
