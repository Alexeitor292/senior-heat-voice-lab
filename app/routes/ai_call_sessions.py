from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.ai_call_sessions import (
    AICallCompletionRequest,
    AICallCompletionResponse,
)
from app.services.ai_call_session_adapter_service import (
    ai_call_session_adapter_service,
)

router = APIRouter(tags=["AI Call Sessions"])


@router.post(
    "/seniors/{senior_id}/ai-call-sessions/complete",
    response_model=AICallCompletionResponse,
)
def complete_ai_call_session(
    senior_id: int,
    payload: AICallCompletionRequest,
):
    result = ai_call_session_adapter_service.complete_call(
        senior_id=senior_id,
        payload=payload,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return result