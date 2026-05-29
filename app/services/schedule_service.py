import json
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app.db.database import SessionLocal
from app.db.models import CheckInSchedule
from app.services.profile_service import profile_service
from app.services.twilio_service import twilio_service


def _schedule_to_dict(schedule: CheckInSchedule) -> dict[str, Any]:
    return {
        "id": schedule.id,
        "senior_id": schedule.senior_id,
        "name": schedule.name,
        "enabled": schedule.enabled,
        "time_of_day": schedule.time_of_day,
        "timezone": schedule.timezone,
        "days_of_week": json.loads(schedule.days_of_week_json),
        "last_run_at": schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        "last_run_status": schedule.last_run_status,
        "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
        "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None,
    }


def _parse_time_of_day(value: str) -> tuple[int, int]:
    """
    Parses HH:MM into hour and minute.
    """

    parts = value.strip().split(":")

    if len(parts) != 2:
        raise ValueError("time_of_day must be in HH:MM format.")

    hour = int(parts[0])
    minute = int(parts[1])

    if hour < 0 or hour > 23:
        raise ValueError("Hour must be between 0 and 23.")

    if minute < 0 or minute > 59:
        raise ValueError("Minute must be between 0 and 59.")

    return hour, minute


def _ensure_utc_aware(value: datetime) -> datetime:
    """
    SQLite often returns datetime values without timezone info.

    Our app stores last_run_at as UTC. If SQLite gives us a naive datetime,
    we explicitly treat it as UTC before converting it to the senior's local
    timezone.
    """

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


class ScheduleService:
    def create_schedule(
        self,
        senior_id: int,
        name: str,
        time_of_day: str,
        timezone_name: str = "America/Los_Angeles",
        days_of_week: list[int] | None = None,
        enabled: bool = True,
    ) -> dict[str, Any] | None:
        senior = profile_service.get_senior(senior_id)

        if not senior:
            return None

        _parse_time_of_day(time_of_day)

        if days_of_week is None:
            days_of_week = [0, 1, 2, 3, 4, 5, 6]

        for day in days_of_week:
            if day < 0 or day > 6:
                raise ValueError("days_of_week values must be between 0 and 6.")

        ZoneInfo(timezone_name)

        with SessionLocal() as db:
            schedule = CheckInSchedule(
                senior_id=senior_id,
                name=name,
                enabled=enabled,
                time_of_day=time_of_day,
                timezone=timezone_name,
                days_of_week_json=json.dumps(days_of_week),
                last_run_at=None,
                last_run_status=None,
            )

            db.add(schedule)
            db.commit()
            db.refresh(schedule)

            return _schedule_to_dict(schedule)

    def list_schedules(
        self,
        senior_id: int | None = None,
    ) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            query = db.query(CheckInSchedule)

            if senior_id is not None:
                query = query.filter(CheckInSchedule.senior_id == senior_id)

            schedules = (
                query
                .order_by(CheckInSchedule.created_at.desc())
                .all()
            )

            return [_schedule_to_dict(schedule) for schedule in schedules]

    def get_schedule(self, schedule_id: int) -> dict[str, Any] | None:
        with SessionLocal() as db:
            schedule = db.get(CheckInSchedule, schedule_id)

            if not schedule:
                return None

            return _schedule_to_dict(schedule)

    def set_schedule_enabled(
        self,
        schedule_id: int,
        enabled: bool,
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            schedule = db.get(CheckInSchedule, schedule_id)

            if not schedule:
                return None

            schedule.enabled = enabled
            db.commit()
            db.refresh(schedule)

            return _schedule_to_dict(schedule)

    def _is_due(
        self,
        schedule: CheckInSchedule,
        now_utc: datetime,
    ) -> bool:
        if not schedule.enabled:
            return False

        now_utc = _ensure_utc_aware(now_utc)

        tz = ZoneInfo(schedule.timezone)
        now_local = now_utc.astimezone(tz)

        days_of_week = json.loads(schedule.days_of_week_json)

        if now_local.weekday() not in days_of_week:
            return False

        hour, minute = _parse_time_of_day(schedule.time_of_day)

        scheduled_local = now_local.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )

        if now_local < scheduled_local:
            return False

        if schedule.last_run_at is None:
            return True

        last_run_utc = _ensure_utc_aware(schedule.last_run_at)
        last_run_local = last_run_utc.astimezone(tz)

        # This is the key guard:
        # if the schedule already ran on the senior's local date, do not run again.
        if last_run_local.date() == now_local.date():
            return False

        return True

    def list_due_schedules(self) -> list[dict[str, Any]]:
        now_utc = datetime.now(timezone.utc)

        with SessionLocal() as db:
            schedules = (
                db.query(CheckInSchedule)
                .filter(CheckInSchedule.enabled.is_(True))
                .all()
            )

            due = [
                schedule
                for schedule in schedules
                if self._is_due(schedule, now_utc)
            ]

            return [_schedule_to_dict(schedule) for schedule in due]

    def run_due_check_ins(self) -> dict[str, Any]:
        """
        Finds due schedules and starts profile-based check-in calls.

        This is manually triggered for now:
        POST /scheduler/run-due-checks
        """

        now_utc = datetime.now(timezone.utc)
        results = []

        with SessionLocal() as db:
            schedules = (
                db.query(CheckInSchedule)
                .filter(CheckInSchedule.enabled.is_(True))
                .all()
            )

            for schedule in schedules:
                if not self._is_due(schedule, now_utc):
                    continue

                senior = profile_service.get_senior(schedule.senior_id)

                if not senior:
                    schedule.last_run_at = now_utc
                    schedule.last_run_status = "failed_senior_not_found"
                    db.commit()

                    results.append({
                        "schedule_id": schedule.id,
                        "senior_id": schedule.senior_id,
                        "started": False,
                        "reason": "Senior profile not found.",
                    })
                    continue

                if not senior["is_active"]:
                    schedule.last_run_at = now_utc
                    schedule.last_run_status = "skipped_senior_inactive"
                    db.commit()

                    results.append({
                        "schedule_id": schedule.id,
                        "senior_id": schedule.senior_id,
                        "started": False,
                        "reason": "Senior profile is inactive.",
                    })
                    continue

                caregiver = profile_service.get_primary_caregiver_for_senior(
                    schedule.senior_id
                )

                try:
                    call = twilio_service.start_senior_speech_check_call(
                        senior_id=senior["id"],
                        senior_phone_number=senior["phone_number"],
                    )

                    session = profile_service.create_check_in_call_session(
                        senior=senior,
                        caregiver=caregiver,
                        senior_call_sid=call.sid,
                    )

                    schedule.last_run_at = now_utc
                    schedule.last_run_status = "call_started"
                    db.commit()

                    results.append({
                        "schedule_id": schedule.id,
                        "senior_id": senior["id"],
                        "senior_name": senior["name"],
                        "caregiver_id": caregiver["id"] if caregiver else None,
                        "caregiver_name": caregiver["name"] if caregiver else None,
                        "started": True,
                        "call_sid": call.sid,
                        "session": session,
                    })

                except Exception as exc:
                    schedule.last_run_at = now_utc
                    schedule.last_run_status = "failed_to_start_call"
                    db.commit()

                    results.append({
                        "schedule_id": schedule.id,
                        "senior_id": senior["id"],
                        "senior_name": senior["name"],
                        "started": False,
                        "reason": str(exc),
                    })

        return {
            "started_count": len([item for item in results if item["started"]]),
            "checked_at": now_utc.isoformat(),
            "results": results,
        }


schedule_service = ScheduleService()