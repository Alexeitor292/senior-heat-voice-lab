from fastapi import APIRouter, HTTPException

from app.config import settings
from app.services.twilio_service import twilio_service

router = APIRouter(prefix="/calls", tags=["Calls"])


@router.post("/start-test-call")
def start_test_call():
    """
    Starts the Step 1/Step 2 test call.

    This call uses the keypad flow:
    Press 1 for yes.
    Press 2 for no.
    """

    try:
        call = twilio_service.start_test_call()

        return {
            "message": "Keypad test call started",
            "call_sid": call.sid,
            "to": settings.test_phone_number,
            "from": settings.twilio_phone_number,
            "next_step": "Answer your phone and press 1 or 2."
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Twilio call: {str(exc)}"
        )


@router.post("/start-speech-test-call")
def start_speech_test_call():
    """
    Starts the Step 3 speech test call.

    This call asks the user to answer out loud.
    Twilio will transcribe the speech and send it to our backend.
    """

    try:
        call = twilio_service.start_speech_test_call()

        return {
            "message": "Speech test call started",
            "call_sid": call.sid,
            "to": settings.test_phone_number,
            "from": settings.twilio_phone_number,
            "next_step": "Answer your phone and speak your response."
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Twilio speech call: {str(exc)}"
        )