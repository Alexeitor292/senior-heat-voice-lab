from fastapi import APIRouter, HTTPException

from app.config import settings
from app.servives.twilio_services import twilio_service

router = APIRouter(prefix="/calls", tags=["Calls"])


@router.post("/start-test-call")
def start_test_call():
    """
    Starts a Step 1 test call.

    This should make your personal phone ring and play
    the scripted heat safety message.
    """

    try:
        call = twilio_service.start_test_call()

        return {
            "message": "Test call started",
            "call_sid": call.sid,
            "to": settings.test_phone_number,
            "from": settings.twilio_phone_number,
            "next_step": "Answer your phone and listen for the heat-check message."
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Twilio call: {str(exc)}"
        )