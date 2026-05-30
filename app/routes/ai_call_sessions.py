from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.ai_call_sessions import (
    AICallCompletionRequest,
    AICallCompletionResponse,
    AICallSessionCompleteRequest,
    AICallSessionStartRequest,
    AICallSessionTurnRequest,
)
from app.services.ai_call_session_adapter_service import (
    ai_call_session_adapter_service,
)

router = APIRouter(tags=["AI Call Sessions"])


@router.post("/seniors/{senior_id}/ai-call-sessions/start")
def start_ai_call_session(
    senior_id: int,
    payload: AICallSessionStartRequest,
):
    result = ai_call_session_adapter_service.start_session(
        senior_id=senior_id,
        payload=payload,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return result


@router.post("/ai-call-sessions/{session_id}/turns")
def append_ai_call_session_turn(
    session_id: int,
    payload: AICallSessionTurnRequest,
):
    result = ai_call_session_adapter_service.append_turn(
        session_id=session_id,
        payload=payload,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="AI call session not found.",
        )

    return result


@router.get("/ai-call-sessions/{session_id}")
def get_ai_call_session(session_id: int):
    result = ai_call_session_adapter_service.get_session(session_id=session_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="AI call session not found.",
        )

    return result


@router.post(
    "/ai-call-sessions/{session_id}/complete",
    response_model=AICallCompletionResponse,
)
def complete_existing_ai_call_session(
    session_id: int,
    payload: AICallSessionCompleteRequest,
):
    result = ai_call_session_adapter_service.complete_existing_session(
        session_id=session_id,
        payload=payload,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="AI call session not found or no transcript turns were captured.",
        )

    return result


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