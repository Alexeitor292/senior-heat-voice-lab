import json
from typing import Any
from uuid import uuid4

from app.db.database import SessionLocal
from app.db.models import CaregiverAlert, CheckIn


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _safe_int(value: str | None) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        return None


class CheckInStoreService:
    def create_check_in(
        self,
        senior_call_sid: str | None,
        from_number: str | None,
        to_number: str | None,
        transcript: str,
        speech_confidence: str | None,
        risk_analysis: dict[str, Any],
        caregiver_alert_required: bool,
    ) -> CheckIn:
        """
        Saves the main senior check-in record.
        """

        with SessionLocal() as db:
            check_in = CheckIn(
                source="twilio_speech_check",
                senior_phone_number=to_number,
                twilio_phone_number=from_number,
                senior_call_sid=senior_call_sid,
                senior_call_status="in-progress",
                transcript=transcript,
                speech_confidence=speech_confidence,
                risk_level=risk_analysis.get("risk_level", "UNKNOWN"),
                reported_symptoms_json=_json_dumps(
                    risk_analysis.get("reported_symptoms", [])
                ),
                red_flags_json=_json_dumps(
                    risk_analysis.get("red_flags", [])
                ),
                orientation_concern=bool(
                    risk_analysis.get("orientation_concern", False)
                ),
                escalation_needed=bool(
                    risk_analysis.get("escalation_needed", False)
                ),
                caregiver_summary=risk_analysis.get("caregiver_summary"),
                recommended_action=risk_analysis.get("recommended_action"),
                confidence_notes=risk_analysis.get("confidence_notes"),
                analyzer=risk_analysis.get("analyzer"),
                raw_analysis_json=_json_dumps(risk_analysis),
                caregiver_alert_required=caregiver_alert_required,
                caregiver_alert_sent=False,
                caregiver_alert_type=None,
                caregiver_alert_id=None,
            )

            db.add(check_in)
            db.commit()
            db.refresh(check_in)

            return check_in

    def create_caregiver_alert(
        self,
        check_in_id: int | None,
        risk_level: str,
        caregiver_phone_number: str,
        payload: dict[str, Any],
    ) -> CaregiverAlert:
        """
        Saves a caregiver alert payload before the caregiver call starts.
        The caregiver Twilio webhook will read this payload by alert_id.
        """

        with SessionLocal() as db:
            alert = CaregiverAlert(
                id=str(uuid4()),
                check_in_id=check_in_id,
                alert_type="voice_call",
                risk_level=risk_level,
                caregiver_phone_number=caregiver_phone_number,
                alert_sent=False,
                delivery_status="created",
                payload_json=_json_dumps(payload),
            )

            db.add(alert)
            db.commit()
            db.refresh(alert)

            return alert

    def caregiver_alert_exists_for_source_call(
        self,
        source_call_sid: str | None,
        alert_kind: str | None = None,
    ) -> bool:
        """
        Prevents duplicate caregiver alerts for the same senior call.

        We avoid adding new columns right now and search the JSON payload text.
        Later, this should become a proper indexed source_call_sid column.
        """

        if not source_call_sid:
            return False

        with SessionLocal() as db:
            query = (
                db.query(CaregiverAlert)
                .filter(CaregiverAlert.payload_json.contains(source_call_sid))
            )

            if alert_kind:
                query = query.filter(CaregiverAlert.payload_json.contains(alert_kind))

            return query.first() is not None

    def mark_caregiver_alert_call_started(
        self,
        alert_id: str,
        caregiver_call_sid: str,
    ) -> None:
        with SessionLocal() as db:
            alert = db.get(CaregiverAlert, alert_id)

            if not alert:
                return

            alert.alert_sent = True
            alert.delivery_status = "call_started"
            alert.caregiver_call_sid = caregiver_call_sid

            if alert.check_in_id:
                check_in = db.get(CheckIn, alert.check_in_id)
                if check_in:
                    check_in.caregiver_alert_sent = True
                    check_in.caregiver_alert_type = "voice_call"
                    check_in.caregiver_alert_id = alert_id

            db.commit()

    def mark_caregiver_alert_failed(
        self,
        alert_id: str,
        error_message: str,
    ) -> None:
        with SessionLocal() as db:
            alert = db.get(CaregiverAlert, alert_id)

            if not alert:
                return

            alert.alert_sent = False
            alert.delivery_status = "failed_to_start"
            alert.error_message = error_message

            db.commit()

    def get_caregiver_alert_payload(
        self,
        alert_id: str,
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            alert = db.get(CaregiverAlert, alert_id)

            if not alert:
                return None

            try:
                return json.loads(alert.payload_json)
            except json.JSONDecodeError:
                return None

    def update_call_status_by_sid(
        self,
        call_sid: str | None,
        call_status: str | None,
        call_duration: str | None,
    ) -> None:
        """
        Updates either:
        - the senior check-in call status, or
        - the caregiver alert call status

        depending on which record owns the Call SID.
        """

        if not call_sid:
            return

        duration = _safe_int(call_duration)

        with SessionLocal() as db:
            check_in = (
                db.query(CheckIn)
                .filter(CheckIn.senior_call_sid == call_sid)
                .first()
            )

            if check_in:
                check_in.senior_call_status = call_status

                if duration is not None:
                    check_in.senior_call_duration_seconds = duration

                db.commit()
                return

            alert = (
                db.query(CaregiverAlert)
                .filter(CaregiverAlert.caregiver_call_sid == call_sid)
                .first()
            )

            if alert:
                alert.caregiver_call_status = call_status

                if duration is not None:
                    alert.caregiver_call_duration_seconds = duration

                if call_status:
                    alert.delivery_status = call_status

                db.commit()
                return

    def check_in_exists_for_call_sid(
        self,
        senior_call_sid: str | None,
    ) -> bool:
        """
        Returns True if a speech check-in record exists for this senior call.

        Used to detect calls that completed but never produced a transcript.
        """

        if not senior_call_sid:
            return False

        with SessionLocal() as db:
            row = (
                db.query(CheckIn)
                .filter(CheckIn.senior_call_sid == senior_call_sid)
                .first()
            )

            return row is not None
            

    def get_recent_check_ins(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Simple helper for debugging from an API endpoint.
        """

        with SessionLocal() as db:
            rows = (
                db.query(CheckIn)
                .order_by(CheckIn.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": row.id,
                    "senior_call_sid": row.senior_call_sid,
                    "senior_phone_number": row.senior_phone_number,
                    "transcript": row.transcript,
                    "speech_confidence": row.speech_confidence,
                    "risk_level": row.risk_level,
                    "caregiver_alert_required": row.caregiver_alert_required,
                    "caregiver_alert_sent": row.caregiver_alert_sent,
                    "caregiver_alert_id": row.caregiver_alert_id,
                    "created_at": row.created_at.isoformat()
                    if row.created_at
                    else None,
                }
                for row in rows
            ]
    
        def check_in_exists_for_call_sid(
            self,
            senior_call_sid: str | None,
        ) -> bool:
            """
            Returns True if a speech check-in record exists for this senior call.

            Used to detect calls that completed but never produced a transcript.
            """

            if not senior_call_sid:
                return False

            with SessionLocal() as db:
                row = (
                    db.query(CheckIn)
                    .filter(CheckIn.senior_call_sid == senior_call_sid)
                    .first()
                )

                return row is not None


checkin_store_service = CheckInStoreService()