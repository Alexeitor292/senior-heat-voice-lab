import json
import re
from typing import Any

from app.db.database import SessionLocal
from app.db.models import VoiceBaselineComparison, VoiceBaselineSample


def _safe_float(value: str | float | None) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def _word_count(text: str | None) -> int:
    if not text:
        return 0

    words = re.findall(r"\b[\w']+\b", text.lower())
    return len(words)


def _comparison_to_dict(row: VoiceBaselineComparison) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "check_in_id": row.check_in_id,
        "baseline_sample_id": row.baseline_sample_id,
        "senior_call_sid": row.senior_call_sid,
        "baseline_call_sid": row.baseline_call_sid,
        "baseline_transcript": row.baseline_transcript,
        "current_transcript": row.current_transcript,
        "baseline_speech_confidence": row.baseline_speech_confidence,
        "current_speech_confidence": row.current_speech_confidence,
        "baseline_word_count": row.baseline_word_count,
        "current_word_count": row.current_word_count,
        "word_count_ratio": row.word_count_ratio,
        "confidence_delta": row.confidence_delta,
        "confidence_drop_detected": row.confidence_drop_detected,
        "shorter_response_detected": row.shorter_response_detected,
        "baseline_deviation_level": row.baseline_deviation_level,
        "reasons": json.loads(row.reasons_json),
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


class BaselineComparisonService:
    def get_latest_captured_baseline(
        self,
        senior_id: int,
    ) -> VoiceBaselineSample | None:
        with SessionLocal() as db:
            return (
                db.query(VoiceBaselineSample)
                .filter(VoiceBaselineSample.senior_id == senior_id)
                .filter(VoiceBaselineSample.status == "captured")
                .filter(VoiceBaselineSample.transcript.isnot(None))
                .order_by(VoiceBaselineSample.created_at.desc())
                .first()
            )

    def build_comparison(
        self,
        senior_id: int,
        current_transcript: str,
        current_speech_confidence: str | None,
        senior_call_sid: str | None = None,
    ) -> dict[str, Any]:
        """
        Compares the current check-in transcript against the latest captured baseline.

        This is intentionally simple:
        - transcript length
        - word count ratio
        - speech confidence drop

        This is not a medical diagnosis.
        """

        baseline = self.get_latest_captured_baseline(senior_id)

        if not baseline:
            return {
                "has_baseline": False,
                "baseline_deviation_level": "UNKNOWN",
                "reasons": ["No captured baseline sample exists for this senior yet."],
            }

        baseline_transcript = baseline.transcript or ""
        baseline_confidence = _safe_float(baseline.speech_confidence)
        current_confidence = _safe_float(current_speech_confidence)

        baseline_words = _word_count(baseline_transcript)
        current_words = _word_count(current_transcript)

        word_count_ratio = None
        if baseline_words > 0:
            word_count_ratio = current_words / baseline_words

        confidence_delta = None
        if baseline_confidence is not None and current_confidence is not None:
            confidence_delta = baseline_confidence - current_confidence

        reasons: list[str] = []
        deviation_level = "GREEN"

        confidence_drop_detected = False
        shorter_response_detected = False

        if current_words == 0:
            deviation_level = "RED"
            reasons.append("No current spoken response was captured.")

        if baseline_words >= 10 and current_words <= 3:
            shorter_response_detected = True
            deviation_level = "RED"
            reasons.append(
                "Current response is extremely short compared with the captured baseline."
            )

        elif word_count_ratio is not None and word_count_ratio < 0.55:
            shorter_response_detected = True

            if deviation_level != "RED":
                deviation_level = "YELLOW"

            reasons.append(
                "Current response is much shorter than the captured baseline."
            )

        if confidence_delta is not None and confidence_delta >= 0.35:
            confidence_drop_detected = True
            deviation_level = "RED"
            reasons.append(
                "Speech confidence dropped sharply compared with the baseline."
            )

        elif confidence_delta is not None and confidence_delta >= 0.20:
            confidence_drop_detected = True

            if deviation_level != "RED":
                deviation_level = "YELLOW"

            reasons.append(
                "Speech confidence is lower than the captured baseline."
            )

        if not reasons:
            reasons.append("Current response is broadly similar to the latest baseline.")

        return {
            "has_baseline": True,
            "baseline_sample_id": baseline.id,
            "baseline_call_sid": baseline.baseline_call_sid,
            "senior_call_sid": senior_call_sid,
            "baseline_transcript": baseline_transcript,
            "current_transcript": current_transcript,
            "baseline_speech_confidence": baseline_confidence,
            "current_speech_confidence": current_confidence,
            "baseline_word_count": baseline_words,
            "current_word_count": current_words,
            "word_count_ratio": word_count_ratio,
            "confidence_delta": confidence_delta,
            "confidence_drop_detected": confidence_drop_detected,
            "shorter_response_detected": shorter_response_detected,
            "baseline_deviation_level": deviation_level,
            "reasons": reasons,
        }

    def save_comparison(
        self,
        senior_id: int,
        check_in_id: int | None,
        comparison: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Saves a baseline comparison if a baseline exists.
        """

        if not comparison.get("has_baseline"):
            return None

        with SessionLocal() as db:
            row = VoiceBaselineComparison(
                senior_id=senior_id,
                check_in_id=check_in_id,
                baseline_sample_id=comparison.get("baseline_sample_id"),
                senior_call_sid=comparison.get("senior_call_sid"),
                baseline_call_sid=comparison.get("baseline_call_sid"),
                baseline_transcript=comparison.get("baseline_transcript"),
                current_transcript=comparison.get("current_transcript"),
                baseline_speech_confidence=comparison.get("baseline_speech_confidence"),
                current_speech_confidence=comparison.get("current_speech_confidence"),
                baseline_word_count=comparison.get("baseline_word_count", 0),
                current_word_count=comparison.get("current_word_count", 0),
                word_count_ratio=comparison.get("word_count_ratio"),
                confidence_delta=comparison.get("confidence_delta"),
                confidence_drop_detected=bool(
                    comparison.get("confidence_drop_detected", False)
                ),
                shorter_response_detected=bool(
                    comparison.get("shorter_response_detected", False)
                ),
                baseline_deviation_level=comparison.get(
                    "baseline_deviation_level",
                    "UNKNOWN",
                ),
                reasons_json=json.dumps(comparison.get("reasons", [])),
                raw_comparison_json=json.dumps(comparison, ensure_ascii=False),
            )

            db.add(row)
            db.commit()
            db.refresh(row)

            return _comparison_to_dict(row)

    def list_comparisons_for_senior(
        self,
        senior_id: int,
    ) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            rows = (
                db.query(VoiceBaselineComparison)
                .filter(VoiceBaselineComparison.senior_id == senior_id)
                .order_by(VoiceBaselineComparison.created_at.desc())
                .all()
            )

            return [_comparison_to_dict(row) for row in rows]


baseline_comparison_service = BaselineComparisonService()