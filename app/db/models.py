from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class SeniorProfile(Base):
    __tablename__ = "senior_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), index=True, nullable=False)

    preferred_language: Mapped[str] = mapped_column(String(20), default="en-US")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class CaregiverProfile(Base):
    __tablename__ = "caregiver_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("senior_profiles.id"),
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), index=True, nullable=False)

    relationship: Mapped[str | None] = mapped_column(String(80), nullable=True)
    alert_priority: Mapped[int] = mapped_column(Integer, default=1)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class CheckInSchedule(Base):
    __tablename__ = "check_in_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("senior_profiles.id"),
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(120), default="Default heat check-in schedule")

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # 24-hour local time for the senior, example: "15:00"
    time_of_day: Mapped[str] = mapped_column(String(10), nullable=False)

    # IANA timezone, example: "America/Los_Angeles"
    timezone: Mapped[str] = mapped_column(String(80), default="America/Los_Angeles")

    # JSON list of integers.
    # Monday = 0, Tuesday = 1, ..., Sunday = 6
    days_of_week_json: Mapped[str] = mapped_column(Text, default="[0,1,2,3,4,5,6]")

    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[str | None] = mapped_column(String(80), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

class CheckInCallSession(Base):
    __tablename__ = "check_in_call_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("senior_profiles.id"),
        index=True,
        nullable=False,
    )

    caregiver_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("caregiver_profiles.id"),
        index=True,
        nullable=True,
    )

    senior_name: Mapped[str] = mapped_column(String(120), nullable=False)
    senior_phone_number: Mapped[str] = mapped_column(String(30), nullable=False)

    caregiver_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    caregiver_phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)

    senior_call_sid: Mapped[str] = mapped_column(String(80), unique=True, index=True)

    status: Mapped[str] = mapped_column(String(40), default="created")
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


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
        onupdate=utc_now,
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
        onupdate=utc_now,
    )