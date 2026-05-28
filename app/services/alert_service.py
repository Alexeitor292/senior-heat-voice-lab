from typing import Any

from app.config import settings
from app.services.alert_store import alert_store
from app.services.twilio_service import twilio_service


class AlertService:
    def should_alert_caregiver(self, risk_level: str) -> bool:
        """
        GREEN means no alert.
        YELLOW, RED, and UNKNOWN should notify the caregiver.
        """

        return risk_level in ["YELLOW", "RED", "UNKNOWN"]

    def build_caregiver_voice_payload(
        self,
        risk_analysis: dict[str, Any],
        transcript: str,
        call_sid: str | None = None
    ) -> dict[str, Any]:
        """
        Builds the payload that will be spoken to the caregiver.

        This is intentionally careful:
        - It does not diagnose heat stroke.
        - It says heat safety concern.
        - It gives a caregiver action.
        """

        risk_level = risk_analysis.get("risk_level", "UNKNOWN")

        caregiver_summary = risk_analysis.get(
            "caregiver_summary",
            "No caregiver summary was generated."
        )

        recommended_action = risk_analysis.get(
            "recommended_action",
            "Please check in with the person."
        )

        reported_symptoms = risk_analysis.get("reported_symptoms", [])
        red_flags = risk_analysis.get("red_flags", [])

        title = {
            "YELLOW": "Heat check-in concern",
            "RED": "Urgent heat safety alert",
            "UNKNOWN": "Heat check-in follow-up needed",
        }.get(risk_level, "Heat check-in alert")

        return {
            "title": title,
            "risk_level": risk_level,
            "transcript": transcript or "No clear transcript captured.",
            "caregiver_summary": caregiver_summary,
            "recommended_action": recommended_action,
            "reported_symptoms": reported_symptoms,
            "red_flags": red_flags,
            "source_call_sid": call_sid,
        }

    def send_caregiver_voice_alert(
        self,
        risk_analysis: dict[str, Any],
        transcript: str,
        call_sid: str | None = None
    ) -> dict[str, Any]:
        """
        Calls the caregiver if the risk level requires escalation.

        Returns a result dictionary instead of throwing so the main
        senior phone call does not fail if the caregiver call fails.
        """

        risk_level = risk_analysis.get("risk_level", "UNKNOWN")

        if not self.should_alert_caregiver(risk_level):
            return {
                "alert_sent": False,
                "alert_type": "voice_call",
                "reason": "Risk level does not require caregiver alert.",
                "risk_level": risk_level
            }

        if not settings.caregiver_test_phone_number:
            return {
                "alert_sent": False,
                "alert_type": "voice_call",
                "reason": "CAREGIVER_TEST_PHONE_NUMBER is not configured.",
                "risk_level": risk_level
            }

        payload = self.build_caregiver_voice_payload(
            risk_analysis=risk_analysis,
            transcript=transcript,
            call_sid=call_sid
        )

        alert_id = alert_store.create_alert(payload)

        try:
            call = twilio_service.start_caregiver_voice_alert_call(
                caregiver_phone_number=settings.caregiver_test_phone_number,
                alert_id=alert_id
            )

            return {
                "alert_sent": True,
                "alert_type": "voice_call",
                "risk_level": risk_level,
                "to": settings.caregiver_test_phone_number,
                "alert_id": alert_id,
                "caregiver_call_sid": call.sid,
                "message_preview": payload
            }

        except Exception as exc:
            return {
                "alert_sent": False,
                "alert_type": "voice_call",
                "risk_level": risk_level,
                "to": settings.caregiver_test_phone_number,
                "alert_id": alert_id,
                "error": str(exc),
                "message_preview": payload
            }


alert_service = AlertService()