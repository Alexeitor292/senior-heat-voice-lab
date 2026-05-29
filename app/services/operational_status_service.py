from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db.database import SessionLocal
from app.db.models import CheckIn, HeatRiskObservation


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _format_time(value: datetime) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


def _human_time(value: datetime | None) -> str:
    if not value:
        return "No check-in recorded"

    now = datetime.now(timezone.utc)

    # SQLite may return naive datetimes even when the SQLAlchemy column says timezone=True.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    delta = now - value

    if delta.days == 0:
        return f"Today, {_format_time(value)}"

    if delta.days == 1:
        return f"Yesterday, {_format_time(value)}"

    if delta.days < 7:
        return f"{delta.days} days ago"

    return value.strftime("%b %d, %Y").replace(" 0", " ")


def _normalize_check_in_risk(value: str | None) -> str:
    if not value:
        return "Unknown"

    normalized = value.strip().upper()

    if normalized in {"LOW", "LOW_RISK", "SAFE"}:
        return "Low"

    if normalized in {"MEDIUM", "MODERATE", "MODERATE_RISK"}:
        return "Moderate"

    if normalized in {"HIGH", "HIGH_RISK"}:
        return "High"

    if normalized in {"EXTREME", "CRITICAL", "URGENT"}:
        return "Extreme"

    return "Unknown"


def _heat_risk_ui_label(value: int | None, label: str | None) -> str:
    if value is not None:
        if value <= 1:
            return "Low"
        if value == 2:
            return "Moderate"
        if value == 3:
            return "High"
        if value >= 4:
            return "Extreme"

    if label:
        lower = label.lower()

        if "extreme" in lower:
            return "Extreme"
        if "major" in lower or "high" in lower:
            return "High"
        if "moderate" in lower:
            return "Moderate"
        if "minor" in lower or "little" in lower or "low" in lower:
            return "Low"

    return "Unknown"


def _status_from_inputs(
    heat_risk: str,
    check_in_risk: str,
    escalation_needed: bool,
    orientation_concern: bool,
    has_support_contact: bool,
    latest_check_in: CheckIn | None,
) -> str:
    no_check_in = latest_check_in is None

    if escalation_needed or orientation_concern:
        return "Urgent"

    if heat_risk == "Extreme":
        return "Urgent"

    if heat_risk == "High" and check_in_risk in {"High", "Extreme"}:
        return "Urgent"

    if heat_risk == "High" and not has_support_contact:
        return "Urgent"

    if heat_risk == "High":
        return "Watch"

    if heat_risk == "Moderate" and no_check_in:
        return "Watch"

    if heat_risk == "Moderate" and check_in_risk in {"Moderate", "High", "Extreme"}:
        return "Watch"

    if check_in_risk in {"High", "Extreme"}:
        return "Watch"

    if heat_risk in {"Low", "Unknown"} and check_in_risk in {"Low", "Unknown"}:
        return "Safe"

    return "Stable"


def _recommended_action(
    status: str,
    heat_risk: str,
    check_in_risk: str,
    has_support_contact: bool,
    latest_check_in: CheckIn | None,
) -> str:
    if latest_check_in and latest_check_in.recommended_action:
        return latest_check_in.recommended_action

    if status == "Urgent" and not has_support_contact:
        return "Operator review + wellness check"

    if status == "Urgent" and has_support_contact:
        return "Contact support network"

    if status == "Watch" and heat_risk in {"High", "Extreme"}:
        return "Call senior"

    if status == "Watch":
        return "Retry check-in"

    if status == "Stable":
        return "Routine check-in"

    return "No action needed"


class OperationalStatusService:
    def get_latest_heat_observation(
        self,
        senior_id: int,
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            row = (
                db.query(HeatRiskObservation)
                .filter(HeatRiskObservation.senior_id == senior_id)
                .order_by(HeatRiskObservation.observed_at.desc())
                .first()
            )

            if not row:
                return None

            return {
                "id": row.id,
                "senior_id": row.senior_id,
                "provider": row.provider,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "heat_risk_value": row.heat_risk_value,
                "heat_risk_label": row.heat_risk_label,
                "observed_at": _iso(row.observed_at),
            }

    def get_latest_check_in(
        self,
        senior_phone_number: str | None,
    ) -> CheckIn | None:
        if not senior_phone_number:
            return None

        with SessionLocal() as db:
            return (
                db.query(CheckIn)
                .filter(CheckIn.senior_phone_number == senior_phone_number)
                .order_by(CheckIn.created_at.desc())
                .first()
            )

    def get_status_for_senior(
        self,
        senior: dict[str, Any],
        has_support_contact: bool,
        fallback_heat_risk: str = "Unknown",
        fallback_status: str = "Stable",
        fallback_recommended_action: str = "Routine check-in",
    ) -> dict[str, Any]:
        senior_id_raw = senior.get("id")

        try:
            senior_id = int(senior_id_raw)
        except (TypeError, ValueError):
            return {
                "heatRisk": fallback_heat_risk,
                "status": fallback_status,
                "latestCheckIn": "Today, 10:18 AM",
                "recommendedAction": fallback_recommended_action,
                "heatRiskValue": None,
                "heatRiskSource": "fallback",
                "latestCheckInRisk": "Unknown",
                "latestCheckInAt": None,
            }

        heat_observation = self.get_latest_heat_observation(senior_id)
        latest_check_in = self.get_latest_check_in(senior.get("phone_number"))

        heat_risk_value = (
            heat_observation.get("heat_risk_value")
            if heat_observation
            else None
        )

        heat_risk_label = (
            heat_observation.get("heat_risk_label")
            if heat_observation
            else None
        )

        heat_risk = _heat_risk_ui_label(heat_risk_value, heat_risk_label)

        if heat_risk == "Unknown":
            heat_risk = fallback_heat_risk

        check_in_risk = _normalize_check_in_risk(
            latest_check_in.risk_level if latest_check_in else None
        )

        escalation_needed = bool(
            latest_check_in.escalation_needed if latest_check_in else False
        )

        orientation_concern = bool(
            latest_check_in.orientation_concern if latest_check_in else False
        )

        status = _status_from_inputs(
            heat_risk=heat_risk,
            check_in_risk=check_in_risk,
            escalation_needed=escalation_needed,
            orientation_concern=orientation_concern,
            has_support_contact=has_support_contact,
            latest_check_in=latest_check_in,
        )

        if not heat_observation and not latest_check_in:
            status = fallback_status

        action = _recommended_action(
            status=status,
            heat_risk=heat_risk,
            check_in_risk=check_in_risk,
            has_support_contact=has_support_contact,
            latest_check_in=latest_check_in,
        )

        if not heat_observation and not latest_check_in:
            action = fallback_recommended_action

        return {
            "heatRisk": heat_risk,
            "status": status,
            "latestCheckIn": _human_time(latest_check_in.created_at)
            if latest_check_in
            else "No check-in recorded",
            "recommendedAction": action,
            "heatRiskValue": heat_risk_value,
            "heatRiskSource": heat_observation.get("provider") if heat_observation else "fallback",
            "latestCheckInRisk": check_in_risk,
            "latestCheckInAt": _iso(latest_check_in.created_at) if latest_check_in else None,
            "escalationNeeded": escalation_needed,
            "orientationConcern": orientation_concern,
        }


operational_status_service = OperationalStatusService()