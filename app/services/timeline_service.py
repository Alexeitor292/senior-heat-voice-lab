from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db.database import SessionLocal
from app.db.models import (
    CheckIn,
    CheckInCallSession,
    EscalationPlan,
    EscalationStep,
    HeatRiskObservation,
    SeniorProfile,
    SupportContact,
)


def _ensure_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value


def _format_time(value: datetime | None) -> str:
    if not value:
        return "Unknown time"

    value = _ensure_aware(value)
    return value.strftime("%I:%M %p").lstrip("0")


def _format_date(value: datetime | None) -> str:
    if not value:
        return "Unknown date"

    value = _ensure_aware(value)
    now = datetime.now(timezone.utc)

    delta_days = (now.date() - value.date()).days

    if delta_days == 0:
        return "Today"

    if delta_days == 1:
        return "Yesterday"

    if delta_days < 7:
        return f"{delta_days} days ago"

    return value.strftime("%b %d, %Y").replace(" 0", " ")


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _event(
    *,
    event_id: str,
    event_type: str,
    title: str,
    description: str | None,
    occurred_at: datetime | None,
    status: str = "info",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": event_id,
        "type": event_type,
        "title": title,
        "description": description,
        "time": _format_time(occurred_at),
        "date": _format_date(occurred_at),
        "status": status,
        "occurredAt": _iso(occurred_at),
        "metadata": metadata or {},
    }


def _check_in_status(row: CheckIn) -> str:
    if row.escalation_needed or row.orientation_concern:
        return "missed"

    risk = (row.risk_level or "").upper()

    if risk in {"HIGH", "EXTREME", "CRITICAL", "URGENT"}:
        return "missed"

    return "success"


def _check_in_title(row: CheckIn) -> str:
    if row.escalation_needed or row.orientation_concern:
        return "High-risk check-in received"

    risk = (row.risk_level or "UNKNOWN").upper()

    if risk in {"HIGH", "EXTREME", "CRITICAL", "URGENT"}:
        return "High-risk check-in received"

    if risk in {"MEDIUM", "MODERATE"}:
        return "Moderate-risk check-in received"

    return "Check-in received"


def _check_in_description(row: CheckIn) -> str:
    parts = []

    if row.risk_level:
        parts.append(f"Risk: {row.risk_level.title()}.")

    if row.recommended_action:
        parts.append(f"Recommended action: {row.recommended_action}")

    if row.orientation_concern:
        parts.append("Orientation concern detected.")

    if row.escalation_needed:
        parts.append("Escalation needed.")

    if not parts and row.transcript:
        return row.transcript[:180]

    return " ".join(parts) or "Check-in completed."


def _heat_status(value: int | None) -> str:
    if value is None:
        return "info"

    if value >= 3:
        return "missed"

    if value == 2:
        return "info"

    return "success"


def _heat_title(value: int | None, label: str | None) -> str:
    if value is None:
        return "Heat risk updated"

    if value >= 4:
        return "Extreme heat risk observed"

    if value == 3:
        return "High heat risk observed"

    if value == 2:
        return "Moderate heat risk observed"

    return "Low heat risk observed"

def _should_include_call_session(
    row: CheckInCallSession,
    check_in_call_sids: set[str],
) -> bool:
    """
    Raw Twilio call sessions are useful only when they explain an exception.

    If a CheckIn exists for the same Call SID, the CheckIn event is more useful.
    Successful/completed call sessions without a check-in usually clutter the
    senior activity feed, so hide them from the main UI timeline.
    """
    if row.senior_call_sid and row.senior_call_sid in check_in_call_sids:
        return False

    status = (row.status or "").lower().strip()

    notable_failure_terms = [
        "failed",
        "no-answer",
        "busy",
        "canceled",
        "cancelled",
        "missed",
        "undelivered",
    ]

    if any(term in status for term in notable_failure_terms):
        return True

    # Hide routine Twilio lifecycle events from the human-facing activity feed.
    routine_terms = [
        "completed",
        "call_started",
        "started",
        "queued",
        "ringing",
        "initiated",
        "in-progress",
    ]

    if any(term in status for term in routine_terms):
        return False

    # Unknown statuses can stay visible for debugging until we understand them.
    return bool(status)


class TimelineService:
    def get_timeline_for_senior(
        self,
        senior_id: int,
        limit: int = 20,
    ) -> list[dict[str, Any]] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            events: list[dict[str, Any]] = []

            check_ins = (
                db.query(CheckIn)
                .filter(CheckIn.senior_phone_number == senior.phone_number)
                .order_by(CheckIn.created_at.desc())
                .limit(limit)
                .all()
            )

            check_in_call_sids = {
                row.senior_call_sid
                for row in check_ins
                if row.senior_call_sid
            }

            for row in check_ins:
                events.append(
                    _event(
                        event_id=f"check-in-{row.id}",
                        event_type="check-in",
                        title=_check_in_title(row),
                        description=_check_in_description(row),
                        occurred_at=row.created_at,
                        status=_check_in_status(row),
                        metadata={
                            "riskLevel": row.risk_level,
                            "seniorCallSid": row.senior_call_sid,
                            "callStatus": row.senior_call_status,
                            "durationSeconds": row.senior_call_duration_seconds,
                            "escalationNeeded": row.escalation_needed,
                            "orientationConcern": row.orientation_concern,
                            "source": row.source,
                        },
                    )
                )

            call_sessions = (
                db.query(CheckInCallSession)
                .filter(CheckInCallSession.senior_id == senior_id)
                .order_by(CheckInCallSession.created_at.desc())
                .limit(limit)
                .all()
            )

            for row in call_sessions:
                if not _should_include_call_session(row, check_in_call_sids):
                    continue

                title = "Check-in call started"

                if row.status and "completed" in row.status.lower():
                    title = "Check-in call completed"
                elif row.status and "no-answer" in row.status.lower():
                    title = "Call attempt missed"

                status = "success"

                if row.status and any(
                    term in row.status.lower()
                    for term in ["failed", "missed", "no-answer", "busy"]
                ):
                    status = "missed"

                events.append(
                    _event(
                        event_id=f"call-session-{row.id}",
                        event_type="call-attempt",
                        title=title,
                        description=f"Call status: {row.status or 'created'}.",
                        occurred_at=row.created_at,
                        status=status,
                        metadata={
                            "seniorCallSid": row.senior_call_sid,
                            "callStatus": row.status,
                            "durationSeconds": row.duration_seconds,
                        },
                    )
                )

            heat_observations = (
                db.query(HeatRiskObservation)
                .filter(HeatRiskObservation.senior_id == senior_id)
                .order_by(HeatRiskObservation.observed_at.desc())
                .limit(limit)
                .all()
            )

            for row in heat_observations:
                events.append(
                    _event(
                        event_id=f"heat-risk-{row.id}",
                        event_type="alert",
                        title=_heat_title(row.heat_risk_value, row.heat_risk_label),
                        description=(
                            f"HeatRisk {row.heat_risk_value}: "
                            f"{row.heat_risk_label}. Source: {row.provider}."
                        ),
                        occurred_at=row.observed_at,
                        status=_heat_status(row.heat_risk_value),
                        metadata={
                            "provider": row.provider,
                            "heatRiskValue": row.heat_risk_value,
                            "heatRiskLabel": row.heat_risk_label,
                            "latitude": row.latitude,
                            "longitude": row.longitude,
                        },
                    )
                )

            support_contacts = (
                db.query(SupportContact)
                .filter(SupportContact.senior_id == senior_id)
                .order_by(SupportContact.created_at.desc())
                .limit(limit)
                .all()
            )

            for row in support_contacts:
                events.append(
                    _event(
                        event_id=f"support-contact-{row.id}",
                        event_type="note",
                        title="Support contact added",
                        description=(
                            f"{row.name} added as {row.relationship or row.contact_type}. "
                            f"Priority {row.priority}."
                        ),
                        occurred_at=row.created_at,
                        status="info",
                        metadata={
                            "contactType": row.contact_type,
                            "priority": row.priority,
                            "canReceiveAlerts": row.can_receive_alerts,
                            "isEmergencyContact": row.is_emergency_contact,
                            "isActive": row.is_active,
                        },
                    )
                )

            plan = (
                db.query(EscalationPlan)
                .filter(EscalationPlan.senior_id == senior_id)
                .first()
            )

            if plan:
                events.append(
                    _event(
                        event_id=f"escalation-plan-{plan.id}",
                        event_type="note",
                        title="Escalation plan saved",
                        description=(
                            f"{plan.living_situation}. {plan.support_mode}. "
                            f"{plan.notes or ''}"
                        ).strip(),
                        occurred_at=plan.updated_at or plan.created_at,
                        status="info",
                        metadata={
                            "livingSituation": plan.living_situation,
                            "supportMode": plan.support_mode,
                            "allowOperatorReview": plan.allow_operator_review,
                            "allowWellnessCheck": plan.allow_wellness_check,
                            "allowEmergencyEscalation": plan.allow_emergency_escalation,
                        },
                    )
                )

                steps = (
                    db.query(EscalationStep)
                    .filter(EscalationStep.plan_id == plan.id)
                    .filter(EscalationStep.is_active.is_(True))
                    .order_by(EscalationStep.step_order.asc())
                    .limit(limit)
                    .all()
                )

                for row in steps:
                    events.append(
                        _event(
                            event_id=f"escalation-step-{row.id}",
                            event_type="note",
                            title="Escalation step configured",
                            description=(
                                f"Step {row.step_order}: {row.action_type} "
                                f"when risk is {row.trigger_level}."
                            ),
                            occurred_at=row.updated_at or row.created_at,
                            status="info",
                            metadata={
                                "stepOrder": row.step_order,
                                "triggerLevel": row.trigger_level,
                                "actionType": row.action_type,
                                "targetContactId": row.target_contact_id,
                            },
                        )
                    )

            events.sort(
                key=lambda item: item.get("occurredAt") or "",
                reverse=True,
            )

            # Keep the senior detail timeline readable.
            # The full endpoint can still request more with ?limit=50 or ?limit=100.
            return events[: min(limit, 12)]


timeline_service = TimelineService()