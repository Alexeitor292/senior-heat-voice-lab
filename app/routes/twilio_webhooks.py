from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from twilio.twiml.voice_response import VoiceResponse

from app.config import settings

router = APIRouter(prefix="/twilio", tags=["Twilio Webhooks"])


def parse_twilio_form(raw_body: bytes) -> dict:
    """
    Twilio sends webhook payloads as application/x-www-form-urlencoded.
    This helper turns the raw body into a simple dictionary.
    """

    parsed = parse_qs(raw_body.decode("utf-8"))

    return {
        key: values[0] if values else None
        for key, values in parsed.items()
    }


@router.post("/voice/heat-check")
async def heat_check_voice():
    """
    Twilio calls this endpoint after the test user answers.

    This version asks the caller to press 1 or 2.
    """

    response = VoiceResponse()

    gather = response.gather(
        input="dtmf",
        num_digits=1,
        timeout=8,
        action=f"{settings.public_base_url}/twilio/voice/heat-check-response",
        method="POST",
    )

    gather.say(
        "Hello. This is your heat safety check-in test. "
        "Are you feeling okay today? "
        "Press 1 for yes. "
        "Press 2 for no."
    )

    response.say(
        "We did not receive a response. "
        "In a future version, this would notify a caregiver. "
        "Goodbye."
    )

    return Response(
        content=str(response),
        media_type="application/xml"
    )


@router.post("/voice/heat-check-response")
async def heat_check_response(request: Request):
    """
    Twilio sends the pressed digit to this endpoint.

    Digit meanings:
    1 = Senior says they are okay
    2 = Senior says they are not okay
    """

    form = parse_twilio_form(await request.body())

    call_sid = form.get("CallSid")
    digit = form.get("Digits")
    from_number = form.get("From")
    to_number = form.get("To")

    print("\nHeat Check Response")
    print("-------------------")
    print(f"Call SID: {call_sid}")
    print(f"Digit pressed: {digit}")
    print(f"From: {from_number}")
    print(f"To: {to_number}")

    response = VoiceResponse()

    if digit == "1":
        print("Result: GREEN")

        response.say(
            "Thank you. We recorded that you are feeling okay today. "
            "This test check-in is complete. Goodbye."
        )

    elif digit == "2":
        print("Result: YELLOW")

        response.say(
            "Thank you for letting us know. "
            "In a future version, we would send a check-in alert to your caregiver. "
            "For this test, we recorded this as a yellow concern. Goodbye."
        )

    else:
        print("Result: UNKNOWN")

        response.say(
            "Sorry, we did not understand that response. "
            "This test check-in is complete. Goodbye."
        )

    return Response(
        content=str(response),
        media_type="application/xml"
    )


@router.post("/status")
async def twilio_status_callback(request: Request):
    """
    Twilio sends call status updates here.
    """

    form = parse_twilio_form(await request.body())

    call_sid = form.get("CallSid")
    call_status = form.get("CallStatus")
    from_number = form.get("From")
    to_number = form.get("To")
    call_duration = form.get("CallDuration")
    direction = form.get("Direction")

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