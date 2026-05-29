import json
from datetime import datetime, timezone
from typing import Any

from app.db.database import SessionLocal
from app.db.models import (
    CaregiverAlert,
    CaregiverProfile,
    CheckIn,
    CheckInCallSession,
    CheckInSchedule,
    HeatRiskObservation,
    HeatTriggeredCall,
    SeniorHeatSettings,
    SeniorProfile,
    VoiceBaselineComparison,
    VoiceBaselineSample,
)


RISK_LEVELS = ["GREEN", "YELLOW", "RED", "UNKNOWN"]


def _json_loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _iso(value: datetime | None) -> str | None:
    if not value:
        return None

    return value.isoformat()


def _senior_to_dict(row: SeniorProfile) -> dict[str, Any]:
    return {
        "id": row.id,
        "name": row.name,
        "phone_number": row.phone_number,
        "preferred_language": row.preferred_language,
        "notes": row.notes,
        "is_active": row.is_active,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _caregiver_to_dict(row: CaregiverProfile) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "name": row.name,
        "phone_number": row.phone_number,
        "relationship": row.relationship,
        "alert_priority": row.alert_priority,
        "is_active": row.is_active,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


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
        "reported_symptoms": _json_loads(row.reported_symptoms_json, []),
        "red_flags": _json_loads(row.red_flags_json, []),
        "orientation_concern": row.orientation_concern,
        "escalation_needed": row.escalation_needed,
        "caregiver_summary": row.caregiver_summary,
        "recommended_action": row.recommended_action,
        "confidence_notes": row.confidence_notes,
        "analyzer": row.analyzer,
        "caregiver_alert_required": row.caregiver_alert_required,
        "caregiver_alert_sent": row.caregiver_alert_sent,
        "caregiver_alert_type": row.caregiver_alert_type,
        "caregiver_alert_id": row.caregiver_alert_id,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _alert_to_dict(row: CaregiverAlert) -> dict[str, Any]:
    payload = _json_loads(row.payload_json, {})

    return {
        "id": row.id,
        "check_in_id": row.check_in_id,
        "alert_type": row.alert_type,
        "alert_kind": payload.get("alert_kind"),
        "risk_level": row.risk_level,
        "caregiver_phone_number": row.caregiver_phone_number,
        "caregiver_call_sid": row.caregiver_call_sid,
        "caregiver_call_status": row.caregiver_call_status,
        "caregiver_call_duration_seconds": row.caregiver_call_duration_seconds,
        "alert_sent": row.alert_sent,
        "delivery_status": row.delivery_status,
        "title": payload.get("title"),
        "senior_name": payload.get("senior_name"),
        "source_call_sid": payload.get("source_call_sid"),
        "caregiver_summary": payload.get("caregiver_summary"),
        "recommended_action": payload.get("recommended_action"),
        "error_message": row.error_message,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


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
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _comparison_to_dict(row: VoiceBaselineComparison) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "check_in_id": row.check_in_id,
        "baseline_sample_id": row.baseline_sample_id,
        "senior_call_sid": row.senior_call_sid,
        "baseline_call_sid": row.baseline_call_sid,
        "baseline_speech_confidence": row.baseline_speech_confidence,
        "current_speech_confidence": row.current_speech_confidence,
        "baseline_word_count": row.baseline_word_count,
        "current_word_count": row.current_word_count,
        "word_count_ratio": row.word_count_ratio,
        "confidence_delta": row.confidence_delta,
        "confidence_drop_detected": row.confidence_drop_detected,
        "shorter_response_detected": row.shorter_response_detected,
        "baseline_deviation_level": row.baseline_deviation_level,
        "reasons": _json_loads(row.reasons_json, []),
        "created_at": _iso(row.created_at),
    }


def _heat_observation_to_dict(row: HeatRiskObservation) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "provider": row.provider,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "heat_risk_value": row.heat_risk_value,
        "heat_risk_label": row.heat_risk_label,
        "source_url": row.source_url,
        "observed_at": _iso(row.observed_at),
    }


def _schedule_to_dict(row: CheckInSchedule) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "name": row.name,
        "enabled": row.enabled,
        "time_of_day": row.time_of_day,
        "timezone": row.timezone,
        "days_of_week": _json_loads(row.days_of_week_json, []),
        "last_run_at": _iso(row.last_run_at),
        "last_run_status": row.last_run_status,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


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


def _heat_trigger_to_dict(row: HeatTriggeredCall) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "local_date": row.local_date,
        "heat_risk_value": row.heat_risk_value,
        "heat_risk_label": row.heat_risk_label,
        "started": row.started,
        "senior_call_sid": row.senior_call_sid,
        "reason": row.reason,
        "created_at": _iso(row.created_at),
    }


class DashboardService:
    def get_summary(self) -> dict[str, Any]:
        with SessionLocal() as db:
            risk_counts = {
                level: db.query(CheckIn).filter(CheckIn.risk_level == level).count()
                for level in RISK_LEVELS
            }

            recent_alerts = (
                db.query(CaregiverAlert)
                .order_by(CaregiverAlert.created_at.desc())
                .limit(5)
                .all()
            )

            recent_check_ins = (
                db.query(CheckIn)
                .order_by(CheckIn.created_at.desc())
                .limit(5)
                .all()
            )

            latest_heat_observation = (
                db.query(HeatRiskObservation)
                .order_by(HeatRiskObservation.observed_at.desc())
                .first()
            )

            return {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "totals": {
                    "seniors": db.query(SeniorProfile).count(),
                    "active_seniors": db.query(SeniorProfile)
                    .filter(SeniorProfile.is_active.is_(True))
                    .count(),
                    "caregivers": db.query(CaregiverProfile).count(),
                    "check_ins": db.query(CheckIn).count(),
                    "caregiver_alerts": db.query(CaregiverAlert).count(),
                    "baseline_samples": db.query(VoiceBaselineSample).count(),
                    "baseline_comparisons": db.query(VoiceBaselineComparison).count(),
                    "enabled_schedules": db.query(CheckInSchedule)
                    .filter(CheckInSchedule.enabled.is_(True))
                    .count(),
                },
                "risk_counts": risk_counts,
                "recent_check_ins": [_check_in_to_dict(row) for row in recent_check_ins],
                "recent_alerts": [_alert_to_dict(row) for row in recent_alerts],
                "latest_heat_observation": (
                    _heat_observation_to_dict(latest_heat_observation)
                    if latest_heat_observation
                    else None
                ),
            }

    def list_senior_cards(self) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            seniors = db.query(SeniorProfile).order_by(SeniorProfile.name.asc()).all()
            cards = []

            for senior in seniors:
                sessions = (
                    db.query(CheckInCallSession)
                    .filter(CheckInCallSession.senior_id == senior.id)
                    .order_by(CheckInCallSession.created_at.desc())
                    .all()
                )

                session_sids = [session.senior_call_sid for session in sessions]

                latest_check_in = None
                if session_sids:
                    latest_check_in = (
                        db.query(CheckIn)
                        .filter(CheckIn.senior_call_sid.in_(session_sids))
                        .order_by(CheckIn.created_at.desc())
                        .first()
                    )

                latest_baseline = (
                    db.query(VoiceBaselineSample)
                    .filter(VoiceBaselineSample.senior_id == senior.id)
                    .order_by(VoiceBaselineSample.created_at.desc())
                    .first()
                )

                latest_comparison = (
                    db.query(VoiceBaselineComparison)
                    .filter(VoiceBaselineComparison.senior_id == senior.id)
                    .order_by(VoiceBaselineComparison.created_at.desc())
                    .first()
                )

                latest_heat = (
                    db.query(HeatRiskObservation)
                    .filter(HeatRiskObservation.senior_id == senior.id)
                    .order_by(HeatRiskObservation.observed_at.desc())
                    .first()
                )

                cards.append(
                    {
                        "senior": _senior_to_dict(senior),
                        "active_caregivers_count": (
                            db.query(CaregiverProfile)
                            .filter(CaregiverProfile.senior_id == senior.id)
                            .filter(CaregiverProfile.is_active.is_(True))
                            .count()
                        ),
                        "enabled_schedules_count": (
                            db.query(CheckInSchedule)
                            .filter(CheckInSchedule.senior_id == senior.id)
                            .filter(CheckInSchedule.enabled.is_(True))
                            .count()
                        ),
                        "latest_check_in": (
                            _check_in_to_dict(latest_check_in)
                            if latest_check_in
                            else None
                        ),
                        "latest_baseline": (
                            _baseline_to_dict(latest_baseline)
                            if latest_baseline
                            else None
                        ),
                        "latest_baseline_comparison": (
                            _comparison_to_dict(latest_comparison)
                            if latest_comparison
                            else None
                        ),
                        "latest_heat_observation": (
                            _heat_observation_to_dict(latest_heat)
                            if latest_heat
                            else None
                        ),
                        "latest_call_session": (
                            _session_to_dict(sessions[0]) if sessions else None
                        ),
                    }
                )

            return cards

    def get_senior_dashboard(self, senior_id: int) -> dict[str, Any] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            caregivers = (
                db.query(CaregiverProfile)
                .filter(CaregiverProfile.senior_id == senior_id)
                .order_by(CaregiverProfile.alert_priority.asc())
                .all()
            )

            schedules = (
                db.query(CheckInSchedule)
                .filter(CheckInSchedule.senior_id == senior_id)
                .order_by(CheckInSchedule.created_at.desc())
                .all()
            )

            sessions = (
                db.query(CheckInCallSession)
                .filter(CheckInCallSession.senior_id == senior_id)
                .order_by(CheckInCallSession.created_at.desc())
                .limit(10)
                .all()
            )

            session_sids = [session.senior_call_sid for session in sessions]

            check_ins = []
            if session_sids:
                check_ins = (
                    db.query(CheckIn)
                    .filter(CheckIn.senior_call_sid.in_(session_sids))
                    .order_by(CheckIn.created_at.desc())
                    .limit(10)
                    .all()
                )

            baselines = (
                db.query(VoiceBaselineSample)
                .filter(VoiceBaselineSample.senior_id == senior_id)
                .order_by(VoiceBaselineSample.created_at.desc())
                .limit(10)
                .all()
            )

            comparisons = (
                db.query(VoiceBaselineComparison)
                .filter(VoiceBaselineComparison.senior_id == senior_id)
                .order_by(VoiceBaselineComparison.created_at.desc())
                .limit(10)
                .all()
            )

            heat_observations = (
                db.query(HeatRiskObservation)
                .filter(HeatRiskObservation.senior_id == senior_id)
                .order_by(HeatRiskObservation.observed_at.desc())
                .limit(10)
                .all()
            )

            heat_triggers = (
                db.query(HeatTriggeredCall)
                .filter(HeatTriggeredCall.senior_id == senior_id)
                .order_by(HeatTriggeredCall.created_at.desc())
                .limit(10)
                .all()
            )

            heat_settings = (
                db.query(SeniorHeatSettings)
                .filter(SeniorHeatSettings.senior_id == senior_id)
                .first()
            )

            return {
                "senior": _senior_to_dict(senior),
                "caregivers": [_caregiver_to_dict(row) for row in caregivers],
                "schedules": [_schedule_to_dict(row) for row in schedules],
                "heat_settings": (
                    {
                        "id": heat_settings.id,
                        "enabled": heat_settings.enabled,
                        "latitude": heat_settings.latitude,
                        "longitude": heat_settings.longitude,
                        "city": heat_settings.city,
                        "state": heat_settings.state,
                        "zip_code": heat_settings.zip_code,
                        "timezone": heat_settings.timezone,
                        "trigger_threshold": heat_settings.trigger_threshold,
                        "created_at": _iso(heat_settings.created_at),
                        "updated_at": _iso(heat_settings.updated_at),
                    }
                    if heat_settings
                    else None
                ),
                "recent_call_sessions": [_session_to_dict(row) for row in sessions],
                "recent_check_ins": [_check_in_to_dict(row) for row in check_ins],
                "recent_baselines": [_baseline_to_dict(row) for row in baselines],
                "recent_baseline_comparisons": [
                    _comparison_to_dict(row) for row in comparisons
                ],
                "recent_heat_observations": [
                    _heat_observation_to_dict(row) for row in heat_observations
                ],
                "recent_heat_triggered_calls": [
                    _heat_trigger_to_dict(row) for row in heat_triggers
                ],
            }

    def list_check_ins(self, limit: int = 25) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            rows = (
                db.query(CheckIn)
                .order_by(CheckIn.created_at.desc())
                .limit(limit)
                .all()
            )

            return [_check_in_to_dict(row) for row in rows]

    def list_alerts(self, limit: int = 25) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            rows = (
                db.query(CaregiverAlert)
                .order_by(CaregiverAlert.created_at.desc())
                .limit(limit)
                .all()
            )

            return [_alert_to_dict(row) for row in rows]

    def list_timeline_for_senior(
        self,
        senior_id: int,
        limit: int = 50,
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            events = []

            sessions = (
                db.query(CheckInCallSession)
                .filter(CheckInCallSession.senior_id == senior_id)
                .order_by(CheckInCallSession.created_at.desc())
                .limit(limit)
                .all()
            )

            session_sids = [session.senior_call_sid for session in sessions]

            for session in sessions:
                events.append(
                    {
                        "type": "call_session",
                        "timestamp": _iso(session.created_at),
                        "title": f"Check-in call {session.status}",
                        "data": _session_to_dict(session),
                    }
                )

            if session_sids:
                check_ins = (
                    db.query(CheckIn)
                    .filter(CheckIn.senior_call_sid.in_(session_sids))
                    .order_by(CheckIn.created_at.desc())
                    .limit(limit)
                    .all()
                )

                for check_in in check_ins:
                    events.append(
                        {
                            "type": "check_in",
                            "timestamp": _iso(check_in.created_at),
                            "title": f"Speech check-in {check_in.risk_level}",
                            "data": _check_in_to_dict(check_in),
                        }
                    )

            for baseline in (
                db.query(VoiceBaselineSample)
                .filter(VoiceBaselineSample.senior_id == senior_id)
                .order_by(VoiceBaselineSample.created_at.desc())
                .limit(limit)
                .all()
            ):
                events.append(
                    {
                        "type": "baseline_sample",
                        "timestamp": _iso(baseline.created_at),
                        "title": f"Baseline sample {baseline.status}",
                        "data": _baseline_to_dict(baseline),
                    }
                )

            for comparison in (
                db.query(VoiceBaselineComparison)
                .filter(VoiceBaselineComparison.senior_id == senior_id)
                .order_by(VoiceBaselineComparison.created_at.desc())
                .limit(limit)
                .all()
            ):
                events.append(
                    {
                        "type": "baseline_comparison",
                        "timestamp": _iso(comparison.created_at),
                        "title": f"Baseline comparison {comparison.baseline_deviation_level}",
                        "data": _comparison_to_dict(comparison),
                    }
                )

            for observation in (
                db.query(HeatRiskObservation)
                .filter(HeatRiskObservation.senior_id == senior_id)
                .order_by(HeatRiskObservation.observed_at.desc())
                .limit(limit)
                .all()
            ):
                events.append(
                    {
                        "type": "heat_risk_observation",
                        "timestamp": _iso(observation.observed_at),
                        "title": f"HeatRisk {observation.heat_risk_value} - {observation.heat_risk_label}",
                        "data": _heat_observation_to_dict(observation),
                    }
                )

            for trigger in (
                db.query(HeatTriggeredCall)
                .filter(HeatTriggeredCall.senior_id == senior_id)
                .order_by(HeatTriggeredCall.created_at.desc())
                .limit(limit)
                .all()
            ):
                events.append(
                    {
                        "type": "heat_triggered_call",
                        "timestamp": _iso(trigger.created_at),
                        "title": (
                            "Heat-triggered check-in started"
                            if trigger.started
                            else "Heat trigger skipped"
                        ),
                        "data": _heat_trigger_to_dict(trigger),
                    }
                )

            events.sort(key=lambda item: item.get("timestamp") or "", reverse=True)

            return {
                "senior": _senior_to_dict(senior),
                "items": events[:limit],
            }


dashboard_service = DashboardService()