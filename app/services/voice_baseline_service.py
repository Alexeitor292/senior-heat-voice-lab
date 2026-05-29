from typing import Any

from app.db.database import SessionLocal
from app.db.models import VoiceBaselineSample
from app.services.profile_service import profile_service


DEFAULT_BASELINE_PROMPT = (
    "Please say this sentence clearly after the beep: "
    "I am feeling okay today. I am inside and comfortable. Today has been a normal day."
)


def _safe_int(value: str | None) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def _baseline_to_dict(row: VoiceBaselineSample) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "senior_name": row.senior_name,
        "senior_phone_number": row.senior_phone_number,
        "baseline_call_sid": row.baseline_call_sid,
        "baseline_call_status": row.baseline_call_status,
        "baseline_call_duration_seconds": row.baseline_call_duration_seconds,
        "prompt_text": row.prompt_text,
        "transcript": row.transcript,
        "speech_confidence": row.speech_confidence,
        "status": row.status,
        "notes": row.notes,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


class VoiceBaselineService:
    def create_pending_baseline_sample(
        self,
        senior_id: int,
        baseline_call_sid: str,
        prompt_text: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any] | None:
        senior = profile_service.get_senior(senior_id)

        if not senior:
            return None

        with SessionLocal() as db:
            row = VoiceBaselineSample(
                senior_id=senior_id,
                senior_name=senior["name"],
                senior_phone_number=senior["phone_number"],
                baseline_call_sid=baseline_call_sid,
                baseline_call_status="call_started",
                prompt_text=prompt_text or DEFAULT_BASELINE_PROMPT,
                transcript=None,
                speech_confidence=None,
                status="pending",
                notes=notes,
            )

            db.add(row)
            db.commit()
            db.refresh(row)

            return _baseline_to_dict(row)

    def get_prompt_for_call_sid(
        self,
        baseline_call_sid: str | None,
    ) -> str:
        if not baseline_call_sid:
            return DEFAULT_BASELINE_PROMPT

        with SessionLocal() as db:
            row = (
                db.query(VoiceBaselineSample)
                .filter(VoiceBaselineSample.baseline_call_sid == baseline_call_sid)
                .first()
            )

            if not row:
                return DEFAULT_BASELINE_PROMPT

            return row.prompt_text

    def mark_baseline_captured(
        self,
        baseline_call_sid: str | None,
        transcript: str | None,
        speech_confidence: str | None,
    ) -> dict[str, Any] | None:
        if not baseline_call_sid:
            return None

        with SessionLocal() as db:
            row = (
                db.query(VoiceBaselineSample)
                .filter(VoiceBaselineSample.baseline_call_sid == baseline_call_sid)
                .first()
            )

            if not row:
                return None

            row.transcript = transcript
            row.speech_confidence = speech_confidence
            row.status = "captured" if transcript else "empty_response"

            db.commit()
            db.refresh(row)

            return _baseline_to_dict(row)

    def update_baseline_call_status_by_sid(
        self,
        baseline_call_sid: str | None,
        call_status: str | None,
        call_duration: str | None,
    ) -> None:
        if not baseline_call_sid:
            return

        duration = _safe_int(call_duration)

        with SessionLocal() as db:
            row = (
                db.query(VoiceBaselineSample)
                .filter(VoiceBaselineSample.baseline_call_sid == baseline_call_sid)
                .first()
            )

            if not row:
                return

            row.baseline_call_status = call_status

            if duration is not None:
                row.baseline_call_duration_seconds = duration

            if call_status in {"no-answer", "busy", "failed", "canceled"} and row.status == "pending":
                row.status = "missed"

            db.commit()

    def list_baselines_for_senior(
        self,
        senior_id: int,
    ) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            rows = (
                db.query(VoiceBaselineSample)
                .filter(VoiceBaselineSample.senior_id == senior_id)
                .order_by(VoiceBaselineSample.created_at.desc())
                .all()
            )

            return [_baseline_to_dict(row) for row in rows]

    def list_recent_baselines(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            rows = (
                db.query(VoiceBaselineSample)
                .order_by(VoiceBaselineSample.created_at.desc())
                .limit(limit)
                .all()
            )

            return [_baseline_to_dict(row) for row in rows]


voice_baseline_service = VoiceBaselineService()