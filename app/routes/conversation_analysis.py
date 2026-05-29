from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.conversation_analysis import (
    ConversationAnalysisRequest,
    ConversationAnalysisStoredResponse,
)
from app.services.ai_conversation_analysis_service import (
    ai_conversation_analysis_service,
)

router = APIRouter(tags=["Conversation Analysis"])


@router.post(
    "/seniors/{senior_id}/conversation-analysis",
    response_model=ConversationAnalysisStoredResponse,
)
def analyze_senior_conversation(
    senior_id: int,
    payload: ConversationAnalysisRequest,
):
    result = ai_conversation_analysis_service.analyze_and_store(
        senior_id=senior_id,
        request=payload,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "message": "Conversation analysis stored.",
        **result,
    }


@router.get("/seniors/{senior_id}/conversation-insights")
def list_senior_conversation_insights(
    senior_id: int,
    limit: int = Query(default=25, ge=1, le=100),
):
    result = ai_conversation_analysis_service.list_insights_for_senior(
        senior_id=senior_id,
        limit=limit,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "senior_id": senior_id,
        "items": result,
    }