from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class CheckIn(Base):
    __tablename__ = "check_ins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    source: Mapped[str] = mapped_column(String(50), default="twilio_speech_check")
    senior_phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    twilio_phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)

    senior_call_sid: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    senior_call_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    senior_call_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    speech_confidence: Mapped[str | None] = mapped_column(String(40), nullable=True)

    risk_level: Mapped[str] = mapped_column(String(20), index=True)
    reported_symptoms_json: Mapped[str] = mapped_column(Text, default="[]")
    red_flags_json: Mapped[str] = mapped_column(Text, default="[]")
    orientation_concern: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_needed: Mapped[bool] = mapped_column(Boolean, default=False)

    caregiver_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    analyzer: Mapped[str | None] = mapped_column(String(80), nullable=True)
    raw_analysis_json: Mapped[str] = mapped_column(Text, default="{}")

    caregiver_alert_required: Mapped[bool] = mapped_column(Boolean, default=False)
    caregiver_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    caregiver_alert_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    caregiver_alert_id: Mapped[str | None] = mapped_column(String(80), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now
    )


class CaregiverAlert(Base):
    __tablename__ = "caregiver_alerts"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, index=True)

    check_in_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    alert_type: Mapped[str] = mapped_column(String(50), default="voice_call")
    risk_level: Mapped[str] = mapped_column(String(20), index=True)

    caregiver_phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    caregiver_call_sid: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    caregiver_call_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    caregiver_call_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_status: Mapped[str | None] = mapped_column(String(80), nullable=True)

    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now
    )