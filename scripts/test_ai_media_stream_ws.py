import asyncio
import json
import time
from urllib.parse import quote

import websockets
from websockets.exceptions import ConnectionClosed

from app.security.ai_stream_token import create_ai_stream_token


async def receiver(ws):
    deadline = time.time() + 8

    while time.time() < deadline:
        try:
            message = await asyncio.wait_for(ws.recv(), timeout=1)
        except asyncio.TimeoutError:
            continue
        except ConnectionClosed as exc:
            print(f"WebSocket closed: code={exc.code}, reason={exc.reason}")
            return

        data = json.loads(message)
        print("RECEIVED FROM BACKEND:")
        print(json.dumps(data, indent=2)[:1000])


async def main():
    senior_id = 1
    stream_token = create_ai_stream_token(senior_id)
    uri = (
        "ws://localhost:8000/twilio/media/ai-check-in"
        f"?stream_token={quote(stream_token)}"
    )

    async with websockets.connect(uri) as ws:
        await ws.send(
            json.dumps(
                {
                    "event": "connected",
                    "protocol": "Call",
                    "version": "1.0.0",
                }
            )
        )

        await ws.send(
            json.dumps(
                {
                    "event": "start",
                    "start": {
                        "streamSid": "MZ_mock_stream_realtime_001",
                        "callSid": "CA_mock_ai_realtime_001",
                        "customParameters": {
                            "senior_id": str(senior_id),
                            "provider": "twilio_media_stream",
                        },
                        "mediaFormat": {
                            "encoding": "audio/x-mulaw",
                            "sampleRate": 8000,
                            "channels": 1,
                        },
                    },
                    "streamSid": "MZ_mock_stream_realtime_001",
                }
            )
        )

        await receiver(ws)

        await ws.send(
            json.dumps(
                {
                    "event": "stop",
                    "streamSid": "MZ_mock_stream_realtime_001",
                    "stop": {
                        "callSid": "CA_mock_ai_realtime_001",
                    },
                }
            )
        )


if __name__ == "__main__":
    asyncio.run(main())