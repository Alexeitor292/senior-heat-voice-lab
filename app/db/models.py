from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
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

class SeniorDemographics(Base):
    __tablename__ = "senior_demographics"

    __table_args__ = (
        UniqueConstraint("senior_id", name="uq_senior_demographics_senior_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("senior_profiles.id"),
        index=True,
        nullable=False,
    )

    # Store as YYYY-MM-DD for now. Later this can become a Date column
    # when Alembic migrations are introduced.
    date_of_birth: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Use explicit age_years for prototype/demo flexibility.
    # If date_of_birth is available, service can compute age from it.
    age_years: Mapped[int | None] = mapped_column(Integer, nullable=True)

    gender: Mapped[str | None] = mapped_column(String(40), nullable=True)
    pronouns: Mapped[str | None] = mapped_column(String(40), nullable=True)

    primary_language: Mapped[str | None] = mapped_column(String(40), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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

class SupportContact(Base):
    __tablename__ = "support_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("senior_profiles.id"),
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), index=True, nullable=False)

    # Examples: daughter, son, neighbor, case worker, front desk, volunteer
    relationship: Mapped[str | None] = mapped_column(String(80), nullable=True)

    # Examples: family, friend, neighbor, facility_staff, case_worker,
    # community_volunteer, operator, emergency_contact
    contact_type: Mapped[str] = mapped_column(String(40), default="family")

    priority: Mapped[int] = mapped_column(Integer, default=1)

    can_receive_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    is_emergency_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class EscalationPlan(Base):
    __tablename__ = "escalation_plans"

    __table_args__ = (
        UniqueConstraint("senior_id", name="uq_escalation_plans_senior_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("senior_profiles.id"),
        index=True,
        nullable=False,
    )

    # Examples: Lives alone, Lives with family, Senior community,
    # Assisted living, Unknown
    living_situation: Mapped[str] = mapped_column(String(60), default="Unknown")

    # Examples: Self-managed, Family supported, Community supported,
    # Facility supported, Operator monitored
    support_mode: Mapped[str] = mapped_column(String(60), default="Self-managed")

    allow_operator_review: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_wellness_check: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_emergency_escalation: Mapped[bool] = mapped_column(Boolean, default=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class EscalationStep(Base):
    __tablename__ = "escalation_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("escalation_plans.id"),
        index=True,
        nullable=False,
    )

    step_order: Mapped[int] = mapped_column(Integer, default=1)

    # Examples: low, moderate, high, urgent
    trigger_level: Mapped[str] = mapped_column(String(40), default="moderate")

    # Examples: retry_senior, call_support_contact, operator_review,
    # dispatch_wellness_check, call_non_emergency, call_emergency_services
    action_type: Mapped[str] = mapped_column(String(60), default="operator_review")

    target_contact_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("support_contacts.id"),
        index=True,
        nullable=True,
    )

    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

class OperatorAction(Base):
    __tablename__ = "operator_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("senior_profiles.id"),
        index=True,
        nullable=False,
    )

    # Examples:
    # call_senior, message_support, wellness_check, operator_review
    action_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)

    # Examples:
    # requested, in_progress, completed, canceled, failed
    status: Mapped[str] = mapped_column(String(40), index=True, default="requested")

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    target_contact_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("support_contacts.id"),
        index=True,
        nullable=True,
    )

    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True)

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

class SeniorHeatSettings(Base):
    __tablename__ = "senior_heat_settings"

    __table_args__ = (
        UniqueConstraint("senior_id", name="uq_senior_heat_settings_senior_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("senior_profiles.id"),
        index=True,
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(40), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    timezone: Mapped[str] = mapped_column(String(80), default="America/Los_Angeles")

    # Default: call when HeatRisk is Moderate or higher.
    # 0 = little/no risk, 1 = minor, 2 = moderate, 3 = major, 4 = extreme
    trigger_threshold: Mapped[int] = mapped_column(Integer, default=2)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

class VoiceBaselineSample(Base):
    __tablename__ = "voice_baseline_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("senior_profiles.id"),
        index=True,
        nullable=False,
    )

    senior_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    senior_phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)

    baseline_call_sid: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    baseline_call_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    baseline_call_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    prompt_text: Mapped[str] = mapped_column(Text)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    speech_confidence: Mapped[str | None] = mapped_column(String(40), nullable=True)

    status: Mapped[str] = mapped_column(String(40), default="pending")

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

class VoiceBaselineComparison(Base):
    __tablename__ = "voice_baseline_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("senior_profiles.id"),
        index=True,
        nullable=False,
    )

    check_in_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    baseline_sample_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)

    senior_call_sid: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    baseline_call_sid: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)

    baseline_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    baseline_speech_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_speech_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    baseline_word_count: Mapped[int] = mapped_column(Integer, default=0)
    current_word_count: Mapped[int] = mapped_column(Integer, default=0)

    word_count_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_delta: Mapped[float | None] = mapped_column(Float, nullable=True)

    confidence_drop_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    shorter_response_detected: Mapped[bool] = mapped_column(Boolean, default=False)

    baseline_deviation_level: Mapped[str] = mapped_column(String(20), default="UNKNOWN")
    reasons_json: Mapped[str] = mapped_column(Text, default="[]")
    raw_comparison_json: Mapped[str] = mapped_column(Text, default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class HeatRiskObservation(Base):
    __tablename__ = "heat_risk_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)

    provider: Mapped[str] = mapped_column(String(40), default="manual")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    heat_risk_value: Mapped[int] = mapped_column(Integer, index=True)
    heat_risk_label: Mapped[str] = mapped_column(String(40))
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    raw_response_json: Mapped[str] = mapped_column(Text, default="{}")

    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class HeatTriggeredCall(Base):
    __tablename__ = "heat_triggered_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    senior_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    local_date: Mapped[str] = mapped_column(String(20), index=True)

    heat_risk_value: Mapped[int] = mapped_column(Integer)
    heat_risk_label: Mapped[str] = mapped_column(String(40))

    started: Mapped[bool] = mapped_column(Boolean, default=False)
    senior_call_sid: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

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