from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from twilio.twiml.voice_response import VoiceResponse

router = APIRouter(prefix="/twilio", tags=["Twilio Webhooks"])


@router.post("/voice/heat-check")
async def heat_check_voice():
    """
    Twilio calls this endpoint after the test user answers.

    This endpoint returns TwiML, which tells Twilio what to say.
    """

    voice = VoiceResponse()

    voice.say(
        "Hello. This is a heat safety check-in test. "
        "This call was triggered from our backend."
    )

    voice.pause(length=1)

    voice.say(
        "In the next version, this call will ask a simple question, "
        "such as whether you are feeling okay today."
    )

    voice.pause(length=1)

    voice.say(
        "For now, this confirms that our backend can start a real phone call. "
        "Goodbye."
    )

    return Response(
        content=str(voice),
        media_type="application/xml"
    )


@router.post("/status")
async def twilio_status_callback(request: Request):
    """
    Twilio sends call status updates here.

    This version avoids request.form() so we do not depend on multipart parsing.
    """

    raw_body = await request.body()
    parsed = parse_qs(raw_body.decode("utf-8"))

    def get_value(key: str):
        values = parsed.get(key)
        return values[0] if values else None

    call_sid = get_value("CallSid")
    call_status = get_value("CallStatus")
    from_number = get_value("From")
    to_number = get_value("To")
    call_duration = get_value("CallDuration")
    direction = get_value("Direction")

    print("\nTwilio Call Status Update")
    print("-------------------------")
    print(f"Call SID: {call_sid}")
    print(f"Status: {call_status}")
    print(f"From: {from_number}")
    print(f"To: {to_number}")
    print(f"Direction: {direction}")
    print(f"Duration: {call_duration}")

    return {
        "received": True,
        "call_sid": call_sid,
        "status": call_status
    }