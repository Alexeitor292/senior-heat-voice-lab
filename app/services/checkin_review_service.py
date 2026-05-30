from __future__ import annotations

import json
from typing import Any

from app.db.database import SessionLocal
from app.db.models import (
    CheckIn,
    ConversationInsight,
    OperatorAction,
    OperatorActionEvidence,
    SeniorProfile,
    TranscriptTurn,
)

def _iso(value):
    return value.isoformat() if value else None


def _load_json(value: str | None, fallback):
    if not value:
        return fallback

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _check_in_to_dict(row: CheckIn) -> dict[str, Any]:
    return {
        "id": row.id,
        "source": row.source,
        "senior_phone_number": row.senior_phone_number,
        "twilio_phone_number": row.twilio_phone_number,
        "senior_call_sid": row.senior_call_sid,
        "senior_call_status": row.senior_call_status,
        "senior_call_duration_seconds": row.senior_call_duration_seconds,
        "transcript": row.transcript,
        "speech_confidence": row.speech_confidence,
        "risk_level": row.risk_level,
        "reported_symptoms": _load_json(row.reported_symptoms_json, []),
        "red_flags": _load_json(row.red_flags_json, []),
        "orientation_concern": row.orientation_concern,
        "escalation_needed": row.escalation_needed,
        "caregiver_summary": row.caregiver_summary,
        "recommended_action": row.recommended_action,
        "confidence_notes": row.confidence_notes,
        "analyzer": row.analyzer,
        "raw_analysis": _load_json(row.raw_analysis_json, {}),
        "caregiver_alert_required": row.caregiver_alert_required,
        "caregiver_alert_sent": row.caregiver_alert_sent,
        "caregiver_alert_type": row.caregiver_alert_type,
        "caregiver_alert_id": row.caregiver_alert_id,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _senior_to_dict(row: SeniorProfile | None) -> dict[str, Any] | None:
    if not row:
        return None

    return {
        "id": row.id,
        "name": row.name,
        "phone_number": row.phone_number,
        "preferred_language": row.preferred_language,
        "notes": row.notes,
        "is_active": row.is_active,
    }


def _insight_to_dict(row: ConversationInsight | None) -> dict[str, Any] | None:
    if not row:
        return None

    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "check_in_id": row.check_in_id,
        "call_session_id": row.call_session_id,
        "senior_call_sid": row.senior_call_sid,
        "safety_risk_level": row.safety_risk_level,
        "safety_confidence": row.safety_confidence,
        "safety_summary": row.safety_summary,
        "safety_escalation_needed": row.safety_escalation_needed,
        "safety_reason_codes": _load_json(row.safety_reason_codes_json, []),
        "relationship_summary": row.relationship_summary,
        "mood_label": row.mood_label,
        "loneliness_signal": row.loneliness_signal,
        "topics_discussed": _load_json(row.topics_discussed_json, []),
        "follow_up_suggestions": _load_json(row.follow_up_suggestions_json, []),
        "recommended_actions": _load_json(row.recommended_actions_json, []),
        "memory_candidates": _load_json(row.memory_candidates_json, []),
        "analyzer": row.analyzer,
        "created_at": _iso(row.created_at),
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


def _operator_action_to_dict(row: OperatorAction) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "action_type": row.action_type,
        "status": row.status,
        "reason": row.reason,
        "note": row.note,
        "target_contact_id": row.target_contact_id,
        "created_by": row.created_by,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }

def _operator_action_evidence_to_dict(row: OperatorActionEvidence) -> dict[str, Any]:
    return {
        "id": row.id,
        "operator_action_id": row.operator_action_id,
        "senior_id": row.senior_id,
        "check_in_id": row.check_in_id,
        "conversation_insight_id": row.conversation_insight_id,
        "source": row.source,
        "reason": row.reason,
        "created_at": _iso(row.created_at),
    }


def _fallback_transcript_turns(check_in: CheckIn) -> list[dict[str, Any]]:
    if not check_in.transcript:
        return []

    turns = []

    for index, line in enumerate(check_in.transcript.splitlines()):
        clean_line = line.strip()

        if not clean_line:
            continue

        speaker = "unknown"
        text = clean_line

        if ":" in clean_line:
            possible_speaker, possible_text = clean_line.split(":", 1)
            speaker = possible_speaker.strip() or "unknown"
            text = possible_text.strip() or clean_line

        turns.append(
            {
                "id": None,
                "senior_id": None,
                "check_in_id": check_in.id,
                "call_session_id": None,
                "senior_call_sid": check_in.senior_call_sid,
                "turn_index": index,
                "speaker": speaker,
                "text": text,
                "started_at_ms": None,
                "ended_at_ms": None,
                "created_at": _iso(check_in.created_at),
            }
        )

    return turns


class CheckInReviewService:
    def get_review(self, check_in_id: int) -> dict[str, Any] | None:
        with SessionLocal() as db:
            check_in = db.get(CheckIn, check_in_id)

            if not check_in:
                return None

            insight = (
                db.query(ConversationInsight)
                .filter(ConversationInsight.check_in_id == check_in_id)
                .order_by(ConversationInsight.created_at.desc())
                .first()
            )

            senior = None

            if insight:
                senior = db.get(SeniorProfile, insight.senior_id)

            if not senior and check_in.senior_phone_number:
                senior = (
                    db.query(SeniorProfile)
                    .filter(SeniorProfile.phone_number == check_in.senior_phone_number)
                    .first()
                )

            transcript_turn_rows = (
                db.query(TranscriptTurn)
                .filter(TranscriptTurn.check_in_id == check_in_id)
                .order_by(TranscriptTurn.turn_index.asc())
                .all()
            )

            transcript_turns = [_turn_to_dict(row) for row in transcript_turn_rows]

            if not transcript_turns:
                transcript_turns = _fallback_transcript_turns(check_in)

            evidence_rows = (
                db.query(OperatorActionEvidence)
                .filter(OperatorActionEvidence.check_in_id == check_in_id)
                .order_by(OperatorActionEvidence.created_at.desc())
                .all()
            )

            evidence_action_ids = [row.operator_action_id for row in evidence_rows]

            related_action_rows = []

            if evidence_action_ids:
                related_action_rows = (
                    db.query(OperatorAction)
                    .filter(OperatorAction.id.in_(evidence_action_ids))
                    .order_by(OperatorAction.created_at.desc())
                    .all()
                )
            else:
                # Backward compatibility for old test records created before evidence tracking.
                related_action_rows = (
                    db.query(OperatorAction)
                    .filter(OperatorAction.note.contains(f"check-in #{check_in_id}"))
                    .order_by(OperatorAction.created_at.desc())
                    .all()
                )

            return {
                "check_in": _check_in_to_dict(check_in),
                "senior": _senior_to_dict(senior),
                "insight": _insight_to_dict(insight),
                "transcript_turns": transcript_turns,
                "operator_actions": [
                    _operator_action_to_dict(row) for row in related_action_rows
                ],
                "operator_action_evidence": [
                    _operator_action_evidence_to_dict(row) for row in evidence_rows
                ],
            }


checkin_review_service = CheckInReviewService()