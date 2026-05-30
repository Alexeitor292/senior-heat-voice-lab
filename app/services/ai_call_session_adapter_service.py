from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from app.db.database import SessionLocal
from app.db.models import CheckIn, CheckInCallSession, SeniorProfile, TranscriptTurn
from app.schemas.ai_call_sessions import (
    AICallCompletionRequest,
    AICallSessionCompleteRequest,
    AICallSessionStartRequest,
    AICallSessionTurnRequest,
)
from app.schemas.conversation_analysis import (
    ConversationAnalysisRequest,
    TranscriptTurnInput,
)
from app.services.ai_conversation_analysis_service import (
    ai_conversation_analysis_service,
)


def _iso(value):
    return value.isoformat() if value else None


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


def _session_to_dict(row: CheckInCallSession) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "caregiver_id": row.caregiver_id,
        "senior_name": row.senior_name,
        "senior_phone_number": row.senior_phone_number,
        "caregiver_name": row.caregiver_name,
        "caregiver_phone_number": row.caregiver_phone_number,
        "senior_call_sid": row.senior_call_sid,
        "status": row.status,
        "duration_seconds": row.duration_seconds,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _turn_to_dict(row: TranscriptTurn) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "check_in_id": row.check_in_id,
        "call_session_id": row.call_session_id,
        "senior_call_sid": row.senior_call_sid,
        "turn_index": row.turn_index,
        "speaker": row.speaker,
        "text": row.text,
        "started_at_ms": row.started_at_ms,
        "ended_at_ms": row.ended_at_ms,
        "created_at": _iso(row.created_at),
    }


def _turn_input_from_row(row: TranscriptTurn) -> TranscriptTurnInput:
    return TranscriptTurnInput(
        speaker=row.speaker,
        text=row.text,
        started_at_ms=row.started_at_ms,
        ended_at_ms=row.ended_at_ms,
    )


class AICallSessionAdapterService:
    def start_session(
        self,
        senior_id: int,
        payload: AICallSessionStartRequest,
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            senior_call_sid = payload.senior_call_sid or f"ai-session-{uuid4()}"

            existing_session = (
                db.query(CheckInCallSession)
                .filter(CheckInCallSession.senior_call_sid == senior_call_sid)
                .first()
            )

            if existing_session:
                existing_session.status = payload.call_status or "in_progress"

                db.commit()
                db.refresh(existing_session)

                return {
                    "message": "AI call session already existed; reused existing session.",
                    "provider": payload.provider,
                    "provider_session_id": payload.provider_session_id,
                    "session": _session_to_dict(existing_session),
                    "raw_provider_payload": payload.raw_provider_payload,
                    "reused_existing_session": True,
                }

            session = CheckInCallSession(
                senior_id=senior.id,
                caregiver_id=None,
                senior_name=senior.name,
                senior_phone_number=senior.phone_number,
                caregiver_name=None,
                caregiver_phone_number=None,
                senior_call_sid=senior_call_sid,
                status=payload.call_status,
                duration_seconds=None,
            )

            db.add(session)
            db.commit()
            db.refresh(session)

            return {
                "message": "AI call session started.",
                "provider": payload.provider,
                "provider_session_id": payload.provider_session_id,
                "session": _session_to_dict(session),
                "raw_provider_payload": payload.raw_provider_payload,
                "reused_existing_session": False,
            }

    def append_turn(
        self,
        session_id: int,
        payload: AICallSessionTurnRequest,
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            session = db.get(CheckInCallSession, session_id)

            if not session:
                return None

            latest_turn = (
                db.query(TranscriptTurn)
                .filter(TranscriptTurn.call_session_id == session_id)
                .order_by(TranscriptTurn.turn_index.desc())
                .first()
            )

            next_index = 0 if not latest_turn else latest_turn.turn_index + 1
            senior_call_sid = payload.senior_call_sid or session.senior_call_sid

            if payload.senior_call_sid and payload.senior_call_sid != session.senior_call_sid:
                session.senior_call_sid = payload.senior_call_sid

            turn = TranscriptTurn(
                senior_id=session.senior_id,
                check_in_id=None,
                call_session_id=session.id,
                senior_call_sid=senior_call_sid,
                turn_index=next_index,
                speaker=payload.speaker,
                text=payload.text,
                started_at_ms=payload.started_at_ms,
                ended_at_ms=payload.ended_at_ms,
            )

            session.status = "in_progress"

            db.add(turn)
            db.commit()
            db.refresh(turn)
            db.refresh(session)

            return {
                "message": "Transcript turn appended.",
                "session": _session_to_dict(session),
                "turn": _turn_to_dict(turn),
                "provider_event_id": payload.provider_event_id,
                "raw_provider_payload": payload.raw_provider_payload,
            }

    def get_session(
        self,
        session_id: int,
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            session = db.get(CheckInCallSession, session_id)

            if not session:
                return None

            turns = (
                db.query(TranscriptTurn)
                .filter(TranscriptTurn.call_session_id == session_id)
                .order_by(TranscriptTurn.turn_index.asc())
                .all()
            )

            check_in = (
                db.query(CheckIn)
                .filter(CheckIn.senior_call_sid == session.senior_call_sid)
                .order_by(CheckIn.created_at.desc())
                .first()
            )

            return {
                "session": _session_to_dict(session),
                "transcript_turns": [_turn_to_dict(turn) for turn in turns],
                "check_in_id": check_in.id if check_in else None,
                "check_in_review_url": f"/check-ins/{check_in.id}" if check_in else None,
            }

    def complete_existing_session(
        self,
        session_id: int,
        payload: AICallSessionCompleteRequest,
    ) -> dict[str, Any] | None:
        transcript_turns: list[TranscriptTurnInput] = []
        session_senior_id: int | None = None
        session_senior_call_sid: str | None = None

        with SessionLocal() as db:
            session = db.get(CheckInCallSession, session_id)

            if not session:
                return None

            if payload.senior_call_sid and payload.senior_call_sid != session.senior_call_sid:
                session.senior_call_sid = payload.senior_call_sid

            session.status = payload.call_status

            if payload.duration_seconds is not None:
                session.duration_seconds = payload.duration_seconds

            db.commit()
            db.refresh(session)

            session_senior_id = session.senior_id
            session_senior_call_sid = session.senior_call_sid

            if payload.transcript_turns is not None:
                transcript_turns = [
                    TranscriptTurnInput(
                        speaker=turn.speaker,
                        text=turn.text,
                        started_at_ms=turn.started_at_ms,
                        ended_at_ms=turn.ended_at_ms,
                    )
                    for turn in payload.transcript_turns
                ]
            else:
                existing_turns = (
                    db.query(TranscriptTurn)
                    .filter(TranscriptTurn.call_session_id == session_id)
                    .order_by(TranscriptTurn.turn_index.asc())
                    .all()
                )

                transcript_turns = [_turn_input_from_row(turn) for turn in existing_turns]

        if not transcript_turns:
            return None

        has_senior_turn = any(
            (turn.speaker or "").lower().strip() in {"senior", "user", "caller"}
            for turn in transcript_turns
        )

        if not has_senior_turn:
            return None

        if session_senior_id is None:
            return None

        analysis_request = ConversationAnalysisRequest(
            senior_call_sid=payload.senior_call_sid or session_senior_call_sid,
            call_session_id=session_id,
            heat_risk_value=payload.heat_risk_value,
            heat_risk_label=payload.heat_risk_label,
            create_operator_actions=payload.create_operator_actions,
            transcript_turns=transcript_turns,
        )

        result = ai_conversation_analysis_service.analyze_and_store(
            senior_id=session_senior_id,
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
                    "senior_call_sid": payload.senior_call_sid or session_senior_call_sid,
                    "call_session_id": session_id,
                    "call_status": payload.call_status,
                    "duration_seconds": payload.duration_seconds,
                    "raw_provider_payload": payload.raw_provider_payload,
                }
                check_in.raw_analysis_json = _json(raw_analysis)

            persisted_session = db.get(CheckInCallSession, session_id)

            if persisted_session:
                persisted_session.status = payload.call_status

                if payload.duration_seconds is not None:
                    persisted_session.duration_seconds = payload.duration_seconds

            db.commit()

        return {
            "message": "AI call session completed and analyzed.",
            "provider": payload.provider,
            "senior_id": session_senior_id,
            "senior_call_sid": payload.senior_call_sid or session_senior_call_sid,
            "call_session_id": session_id,
            "check_in_id": result["check_in_id"],
            "insight_id": result["insight_id"],
            "check_in_review_url": f"/check-ins/{result['check_in_id']}",
            "analysis": result["analysis"],
            "operator_actions_created": result.get("operator_actions_created", []),
            "operator_actions_updated": result.get("operator_actions_updated", []),
            "operator_action_evidence": result.get("operator_action_evidence", []),
        }

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
            "operator_action_evidence": result.get("operator_action_evidence", []),
        }


ai_call_session_adapter_service = AICallSessionAdapterService()