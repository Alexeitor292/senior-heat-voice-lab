import json
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from twilio.twiml.voice_response import VoiceResponse

from app.config import settings
from app.services.alert_service import alert_service
from app.services.alert_store import alert_store
from app.services.risk_analysis_service import risk_analysis_service

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


@router.post("/voice/heat-check")
async def heat_check_voice():
    """
    Step 2 keypad check-in.
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
    Step 3, Step 4, and Step 5 speech check-in.
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
    Step 5 speech response handler.

    Twilio sends the speech transcript here as SpeechResult.
    We send the transcript to the LLM for structured risk analysis.
    If the risk is YELLOW, RED, or UNKNOWN, we call the caregiver.
    """

    form = parse_twilio_form(await request.body())

    call_sid = form.get("CallSid")
    speech_result = form.get("SpeechResult")
    confidence = form.get("Confidence")
    from_number = form.get("From")
    to_number = form.get("To")

    analysis = risk_analysis_service.analyze_transcript(
        transcript=speech_result or "",
        speech_confidence=confidence
    )

    alert_result = alert_service.send_caregiver_voice_alert(
        risk_analysis=analysis,
        transcript=speech_result or "",
        call_sid=call_sid
    )

    print("\nHeat Check Speech Response")
    print("--------------------------")
    print(f"Call SID: {call_sid}")
    print(f"From: {from_number}")
    print(f"To: {to_number}")
    print(f"SpeechResult: {speech_result}")
    print(f"Confidence: {confidence}")

    print("\nStructured Risk Analysis")
    print("------------------------")
    print(json.dumps(analysis, indent=2))

    print("\nCaregiver Voice Alert Result")
    print("----------------------------")
    print(json.dumps(alert_result, indent=2))

    risk_level = analysis.get("risk_level", "UNKNOWN")
    alert_sent = alert_result.get("alert_sent", False)

    response = VoiceResponse()

    if risk_level == "GREEN":
        response.say(
            "Thank you. We captured your spoken response. "
            "For this test, the result looks normal. Goodbye."
        )

    elif risk_level == "YELLOW":
        if alert_sent:
            response.say(
                "Thank you. We captured your spoken response. "
                "For this test, we recorded a check-in concern and called the caregiver. "
                "Goodbye."
            )
        else:
            response.say(
                "Thank you. We captured your spoken response. "
                "For this test, we recorded a check-in concern. "
                "A caregiver call would be made in the full version. Goodbye."
            )

    elif risk_level == "RED":
        if alert_sent:
            response.say(
                "Thank you. We captured your spoken response. "
                "For this test, we recorded a high concern and called the caregiver. "
                "Goodbye."
            )
        else:
            response.say(
                "Thank you. We captured your spoken response. "
                "For this test, we recorded a high concern. "
                "An urgent caregiver call would be made in the full version. Goodbye."
            )

    else:
        if alert_sent:
            response.say(
                "Thank you. We were not able to clearly assess the response. "
                "For this test, we called the caregiver for follow-up. Goodbye."
            )
        else:
            response.say(
                "Thank you. We were not able to clearly assess the response. "
                "In a future version, this would trigger a caregiver follow-up. Goodbye."
            )

    return Response(
        content=str(response),
        media_type="application/xml"
    )


@router.post("/voice/caregiver-alert")
async def caregiver_alert_voice(alert_id: str):
    """
    Twilio calls this endpoint when the caregiver answers.

    It reads the alert payload out loud.
    """

    payload = alert_store.get_alert(alert_id)

    response = VoiceResponse()

    if not payload:
        response.say(
            "This is a heat safety alert test, but the alert details could not be found. "
            "Please check the dashboard or contact the system administrator. Goodbye."
        )

        return Response(
            content=str(response),
            media_type="application/xml"
        )

    title = payload.get("title", "Heat check-in alert")
    risk_level = payload.get("risk_level", "UNKNOWN")
    transcript = payload.get("transcript", "No clear transcript captured.")
    caregiver_summary = payload.get(
        "caregiver_summary",
        "No caregiver summary was generated."
    )
    recommended_action = payload.get(
        "recommended_action",
        "Please check in with the person."
    )
    reported_symptoms = payload.get("reported_symptoms", [])
    red_flags = payload.get("red_flags", [])

    response.say(
        "This is a caregiver alert from the heat safety check-in system."
    )

    response.pause(length=1)

    response.say(
        f"{title}. Risk level: {risk_level}."
    )

    response.pause(length=1)

    response.say(
        f"The caller said: {transcript}"
    )

    response.pause(length=1)

    response.say(
        f"Summary: {caregiver_summary}"
    )

    response.pause(length=1)

    if reported_symptoms:
        response.say(
            f"Reported symptoms include: {', '.join(reported_symptoms)}."
        )
        response.pause(length=1)

    if red_flags:
        response.say(
            f"Urgent warning signs include: {', '.join(red_flags)}."
        )
        response.pause(length=1)

    response.say(
        f"Recommended action: {recommended_action}"
    )

    response.pause(length=1)

    response.say(
        "This is not a medical diagnosis. "
        "Please use your judgment and contact emergency services if the person appears to be in immediate danger. "
        "Goodbye."
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