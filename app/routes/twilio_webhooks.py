from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from twilio.twiml.voice_response import VoiceResponse

from app.config import settings

router = APIRouter(prefix="/twilio", tags=["Twilio Webhooks"])


def parse_twilio_form(raw_body: bytes) -> dict:
    """
    Twilio sends webhook payloads as application/x-www-form-urlencoded.

    This helper turns the raw request body into a regular dictionary.
    """

    parsed = parse_qs(raw_body.decode("utf-8"))

    return {
        key: values[0] if values else None
        for key, values in parsed.items()
    }


def classify_demo_speech_risk(transcript: str) -> dict:
    """
    Very simple demo-only risk classifier.

    This is not AI.
    This is not medical diagnosis.
    This is just a temporary keyword check so we can test the workflow.
    """

    if not transcript:
        return {
            "risk_level": "UNKNOWN",
            "reason": "No speech transcript received."
        }

    text = transcript.lower()

    red_keywords = [
        "confused",
        "can't think",
        "cannot think",
        "passed out",
        "fainted",
        "seizure",
        "collapsed",
        "can't stand",
        "cannot stand"
    ]

    yellow_keywords = [
        "dizzy",
        "weak",
        "nauseous",
        "nausea",
        "headache",
        "tired",
        "hot",
        "dehydrated",
        "thirsty",
        "not okay",
        "not feeling good",
        "sick"
    ]

    for keyword in red_keywords:
        if keyword in text:
            return {
                "risk_level": "RED",
                "reason": f"Detected urgent keyword: {keyword}"
            }

    for keyword in yellow_keywords:
        if keyword in text:
            return {
                "risk_level": "YELLOW",
                "reason": f"Detected concern keyword: {keyword}"
            }

    return {
        "risk_level": "GREEN",
        "reason": "No concern keywords detected in this demo."
    }


@router.post("/voice/heat-check")
async def heat_check_voice():
    """
    Step 2 keypad check-in.

    Twilio calls this endpoint after the test user answers.
    This version asks the caller to press 1 or 2.
    """

    response = VoiceResponse()

    gather = response.gather(
        input="dtmf",
        num_digits=1,
        timeout=8,
        action=f"{settings.public_base_url.rstrip('/')}/twilio/voice/heat-check-response",
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
    Step 2 keypad response handler.

    Digit meanings:
    1 = Senior says they are okay
    2 = Senior says they are not okay
    """

    form = parse_twilio_form(await request.body())

    call_sid = form.get("CallSid")
    digit = form.get("Digits")
    from_number = form.get("From")
    to_number = form.get("To")

    print("\nHeat Check Keypad Response")
    print("--------------------------")
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


@router.post("/voice/heat-check-speech")
async def heat_check_speech():
    """
    Step 3 speech check-in.

    Twilio calls this endpoint after the test user answers.
    This version asks the caller to respond by speaking.
    """

    response = VoiceResponse()

    gather = response.gather(
        input="speech",
        timeout=5,
        speech_timeout="auto",
        language="en-US",
        action=f"{settings.public_base_url.rstrip('/')}/twilio/voice/heat-check-speech-response",
        method="POST",
    )

    gather.say(
        "Hello. This is your speech-based heat safety check-in test. "
        "Please answer this question out loud. "
        "How are you feeling today?"
    )

    response.say(
        "We did not receive a spoken response. "
        "In a future version, this would trigger a caregiver follow-up. "
        "Goodbye."
    )

    return Response(
        content=str(response),
        media_type="application/xml"
    )


@router.post("/voice/heat-check-speech-response")
async def heat_check_speech_response(request: Request):
    """
    Step 3 speech response handler.

    Twilio sends the speech transcript here as SpeechResult.
    """

    form = parse_twilio_form(await request.body())

    call_sid = form.get("CallSid")
    speech_result = form.get("SpeechResult")
    confidence = form.get("Confidence")
    from_number = form.get("From")
    to_number = form.get("To")

    risk = classify_demo_speech_risk(speech_result or "")

    print("\nHeat Check Speech Response")
    print("--------------------------")
    print(f"Call SID: {call_sid}")
    print(f"From: {from_number}")
    print(f"To: {to_number}")
    print(f"SpeechResult: {speech_result}")
    print(f"Confidence: {confidence}")
    print(f"Demo Risk Level: {risk['risk_level']}")
    print(f"Demo Reason: {risk['reason']}")

    response = VoiceResponse()

    if risk["risk_level"] == "GREEN":
        response.say(
            "Thank you. We captured your spoken response. "
            "For this test, the result looks normal. Goodbye."
        )

    elif risk["risk_level"] == "YELLOW":
        response.say(
            "Thank you. We captured your spoken response. "
            "For this test, we recorded a yellow concern. "
            "In a future version, this would notify a caregiver. Goodbye."
        )

    elif risk["risk_level"] == "RED":
        response.say(
            "Thank you. We captured your spoken response. "
            "For this test, we recorded a high concern. "
            "In a future version, this would trigger an urgent caregiver alert. Goodbye."
        )

    else:
        response.say(
            "Thank you. We were not able to clearly understand the response. "
            "In a future version, this would trigger a follow-up check. Goodbye."
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