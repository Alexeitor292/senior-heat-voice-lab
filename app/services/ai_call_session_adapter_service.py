from __future__ import annotations

import json
from typing import Any

from app.db.database import SessionLocal
from app.db.models import CheckIn, CheckInCallSession
from app.schemas.ai_call_sessions import AICallCompletionRequest
from app.schemas.conversation_analysis import (
    ConversationAnalysisRequest,
    TranscriptTurnInput,
)
from app.services.ai_conversation_analysis_service import (
    ai_conversation_analysis_service,
)


def _load_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}

    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return {}

    if isinstance(loaded, dict):
        return loaded

    return {}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


class AICallSessionAdapterService:
    def complete_call(
        self,
        senior_id: int,
        payload: AICallCompletionRequest,
    ) -> dict[str, Any] | None:
        analysis_request = ConversationAnalysisRequest(
            senior_call_sid=payload.senior_call_sid,
            call_session_id=payload.call_session_id,
            heat_risk_value=payload.heat_risk_value,
            heat_risk_label=payload.heat_risk_label,
            create_operator_actions=payload.create_operator_actions,
            transcript_turns=[
                TranscriptTurnInput(
                    speaker=turn.speaker,
                    text=turn.text,
                    started_at_ms=turn.started_at_ms,
                    ended_at_ms=turn.ended_at_ms,
                )
                for turn in payload.transcript_turns
            ],
        )

        result = ai_conversation_analysis_service.analyze_and_store(
            senior_id=senior_id,
            request=analysis_request,
        )

        if not result:
            return None

        check_in_id = result["check_in_id"]

        with SessionLocal() as db:
            check_in = db.get(CheckIn, check_in_id)

            if check_in:
                check_in.senior_call_status = payload.call_status

                if payload.duration_seconds is not None:
                    check_in.senior_call_duration_seconds = payload.duration_seconds

                raw_analysis = _load_json(check_in.raw_analysis_json)
                raw_analysis["_call_adapter"] = {
                    "provider": payload.provider,
                    "provider_session_id": payload.provider_session_id,
                    "senior_call_sid": payload.senior_call_sid,
                    "call_session_id": payload.call_session_id,
                    "call_status": payload.call_status,
                    "duration_seconds": payload.duration_seconds,
                    "raw_provider_payload": payload.raw_provider_payload,
                }
                check_in.raw_analysis_json = _json(raw_analysis)

            if payload.call_session_id:
                call_session = db.get(CheckInCallSession, payload.call_session_id)

                if call_session:
                    call_session.status = payload.call_status

                    if payload.duration_seconds is not None:
                        call_session.duration_seconds = payload.duration_seconds

            db.commit()

        return {
            "message": "AI call session completed and analyzed.",
            "provider": payload.provider,
            "senior_id": senior_id,
            "senior_call_sid": payload.senior_call_sid,
            "call_session_id": payload.call_session_id,
            "check_in_id": result["check_in_id"],
            "insight_id": result["insight_id"],
            "check_in_review_url": f"/check-ins/{result['check_in_id']}",
            "analysis": result["analysis"],
            "operator_actions_created": result.get("operator_actions_created", []),
            "operator_actions_updated": result.get("operator_actions_updated", []),
        }


ai_call_session_adapter_service = AICallSessionAdapterService()