import json
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from twilio.twiml.voice_response import VoiceResponse

from app.config import settings
from app.services.alert_service import alert_service
from app.services.checkin_store_service import checkin_store_service
from app.services.profile_service import profile_service
from app.services.risk_analysis_service import risk_analysis_service
from app.services.voice_baseline_service import voice_baseline_service

router = APIRouter(prefix="/twilio", tags=["Twilio Webhooks"])


NO_ANSWER_STATUSES = {
    "no-answer",
    "busy",
    "failed",
    "canceled",
}

def should_trigger_incomplete_call_alert(
    call_status: str | None,
    call_sid: str | None,
) -> bool:
    """
    Handles cases where Twilio marks the call completed,
    but the senior never completed the spoken check-in.

    Example:
    - voicemail picked up
    - senior hung up
    - no speech response was captured
    """

    if call_status != "completed":
        return False

    return not checkin_store_service.check_in_exists_for_call_sid(call_sid)


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
async def heat_check_speech(senior_id: int | None = None):
    """
    Step 3 through Step 11 speech check-in.

    If senior_id is present, this is a profile-based call.
    If senior_id is missing, this is the legacy .env test call.
    """

    response = VoiceResponse()

    action_url = (
        f"{settings.public_base_url.rstrip()}"
        "/twilio/voice/heat-check-speech-response"
    )

    if senior_id is not None:
        action_url = f"{action_url}?senior_id={senior_id}"

    gather = response.gather(
        input="speech",
        timeout=5,
        speech_timeout="auto",
        language="en-US",
        action=action_url,
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
async def heat_check_speech_response(
    request: Request,
    senior_id: int | None = None,
):
    """
    Speech response handler.

    Twilio sends the speech transcript here as SpeechResult.
    We analyze the transcript, save the check-in, and call the
    profile caregiver if this is a profile-based check-in.
    """

    form = parse_twilio_form(await request.body())

    call_sid = form.get("CallSid")
    speech_result = form.get("SpeechResult") or ""
    confidence = form.get("Confidence")
    from_number = form.get("From")
    to_number = form.get("To")

    alert_context = None

    if senior_id is not None:
        alert_context = profile_service.get_alert_context_for_senior(senior_id)

    if alert_context is None:
        alert_context = profile_service.get_alert_context_for_call_sid(call_sid)

    senior_name = None
    caregiver_phone_number = None

    if alert_context:
        senior = alert_context.get("senior")
        caregiver = alert_context.get("caregiver")

        if senior:
            senior_name = senior.get("name")

        if caregiver:
            caregiver_phone_number = caregiver.get("phone_number")

    analysis = risk_analysis_service.analyze_transcript(
        transcript=speech_result,
        speech_confidence=confidence,
    )

    risk_level = analysis.get("risk_level", "UNKNOWN")
    caregiver_alert_required = alert_service.should_alert_caregiver(risk_level)

    check_in = checkin_store_service.create_check_in(
        senior_call_sid=call_sid,
        from_number=from_number,
        to_number=to_number,
        transcript=speech_result,
        speech_confidence=confidence,
        risk_analysis=analysis,
        caregiver_alert_required=caregiver_alert_required,
    )

    alert_result = alert_service.send_caregiver_voice_alert(
        risk_analysis=analysis,
        transcript=speech_result,
        call_sid=call_sid,
        check_in_id=check_in.id,
        caregiver_phone_number=caregiver_phone_number,
        senior_name=senior_name,
    )

    print("\nHeat Check Speech Response")
    print("--------------------------")
    print(f"Check-in ID: {check_in.id}")
    print(f"Profile senior_id: {senior_id}")
    print(f"Profile senior_name: {senior_name}")
    print(f"Profile caregiver_phone_number: {caregiver_phone_number}")
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
    The payload is stored in SQLite.
    """

    payload = checkin_store_service.get_caregiver_alert_payload(alert_id)

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
    senior_name = payload.get("senior_name")
    transcript = payload.get("transcript", "No clear transcript captured.")
    caregiver_summary = payload.get(
        "caregiver_summary",
        "No caregiver summary was generated.",
    )
    recommended_action = payload.get(
        "recommended_action",
        "Please check in with the person.",
    )
    reported_symptoms = payload.get("reported_symptoms", [])
    red_flags = payload.get("red_flags", [])

    senior_phrase = senior_name or "the caller"

    response.say(
        "This is a caregiver alert from the heat safety check-in system."
    )

    response.pause(length=1)

    response.say(
        f"{title}. Risk level: {risk_level}."
    )

    response.pause(length=1)

    response.say(
        f"This alert is for {senior_phrase}."
    )

    response.pause(length=1)

    response.say(
        f"{senior_phrase} said: {transcript}"
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

@router.post("/voice/baseline")
async def baseline_voice(
    request: Request,
    senior_id: int | None = None,
):
    """
    Baseline voice sample collection call.

    Twilio calls this endpoint when the senior answers the baseline call.
    """

    form = parse_twilio_form(await request.body())
    call_sid = form.get("CallSid")

    prompt_text = voice_baseline_service.get_prompt_for_call_sid(call_sid)

    response = VoiceResponse()

    action_url = (
        f"{settings.public_base_url.rstrip()}"
        "/twilio/voice/baseline-response"
    )

    if senior_id is not None:
        action_url = f"{action_url}?senior_id={senior_id}"

    gather = response.gather(
        input="speech",
        timeout=5,
        speech_timeout="auto",
        language="en-US",
        action=action_url,
        method="POST",
    )

    gather.say(
        "Hello. This is a baseline voice sample collection test. "
        "This is not a medical check-in. "
        "We are collecting a normal healthy voice sample for future comparison."
    )

    response.pause(length=1)

    gather.say(prompt_text)

    response.say(
        "We did not receive a spoken baseline sample. "
        "Please try again later. Goodbye."
    )

    return Response(
        content=str(response),
        media_type="application/xml",
    )


@router.post("/voice/baseline-response")
async def baseline_voice_response(
    request: Request,
    senior_id: int | None = None,
):
    """
    Twilio sends the baseline speech transcript here as SpeechResult.
    """

    form = parse_twilio_form(await request.body())

    call_sid = form.get("CallSid")
    speech_result = form.get("SpeechResult") or ""
    confidence = form.get("Confidence")
    from_number = form.get("From")
    to_number = form.get("To")

    baseline = voice_baseline_service.mark_baseline_captured(
        baseline_call_sid=call_sid,
        transcript=speech_result,
        speech_confidence=confidence,
    )

    print("\nBaseline Voice Response")
    print("-----------------------")
    print(f"Senior ID: {senior_id}")
    print(f"Call SID: {call_sid}")
    print(f"From: {from_number}")
    print(f"To: {to_number}")
    print(f"SpeechResult: {speech_result}")
    print(f"Confidence: {confidence}")
    print(f"Baseline saved: {baseline}")

    response = VoiceResponse()

    if speech_result:
        response.say(
            "Thank you. We captured your baseline voice sample. "
            "This baseline collection test is complete. Goodbye."
        )
    else:
        response.say(
            "Thank you. We were not able to clearly capture the baseline voice sample. "
            "Please try again later. Goodbye."
        )

    return Response(
        content=str(response),
        media_type="application/xml",
    )

@router.post("/status")
async def twilio_status_callback(request: Request):
    """
    Twilio sends call status updates here.

    If a profile-based senior check-in call ends as no-answer/busy/failed/canceled,
    we call the caregiver with a follow-up alert.
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

    checkin_store_service.update_call_status_by_sid(
        call_sid=call_sid,
        call_status=call_status,
        call_duration=call_duration,
    )

    voice_baseline_service.update_baseline_call_status_by_sid(
        baseline_call_sid=call_sid,
        call_status=call_status,
        call_duration=call_duration,
    )

    profile_service.update_call_session_status(
        senior_call_sid=call_sid,
        status=call_status,
        duration_seconds=call_duration,
    )

    is_failed_call = call_status in NO_ANSWER_STATUSES
    is_completed_without_checkin = should_trigger_incomplete_call_alert(
        call_status=call_status,
        call_sid=call_sid,
    )

    if is_failed_call or is_completed_without_checkin:
        alert_context = profile_service.get_alert_context_for_call_sid(call_sid)

        if alert_context:
            senior = alert_context.get("senior")
            caregiver = alert_context.get("caregiver")

            senior_name = senior.get("name") if senior else None
            caregiver_phone_number = caregiver.get("phone_number") if caregiver else None

            alert_status = call_status

            if is_completed_without_checkin:
                alert_status = "completed_without_speech_response"

            no_answer_alert_result = alert_service.send_no_answer_caregiver_voice_alert(
                senior_name=senior_name,
                caregiver_phone_number=caregiver_phone_number,
                call_sid=call_sid,
                call_status=alert_status,
            )

            print("\nMissed or Incomplete Check-In Caregiver Alert Result")
            print("----------------------------------------------------")
            print(json.dumps(no_answer_alert_result, indent=2))

        else:
            print("\nMissed/incomplete call status received, but no profile call session was found.")
            print("Skipping caregiver missed-check-in alert.")