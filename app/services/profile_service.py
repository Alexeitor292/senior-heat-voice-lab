from typing import Any

from app.db.database import SessionLocal
from app.db.models import CaregiverProfile, CheckInCallSession, SeniorProfile


def _safe_int(value: str | None) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def senior_to_dict(senior: SeniorProfile) -> dict[str, Any]:
    return {
        "id": senior.id,
        "name": senior.name,
        "phone_number": senior.phone_number,
        "preferred_language": senior.preferred_language,
        "notes": senior.notes,
        "is_active": senior.is_active,
        "created_at": senior.created_at.isoformat() if senior.created_at else None,
        "updated_at": senior.updated_at.isoformat() if senior.updated_at else None,
    }


def caregiver_to_dict(caregiver: CaregiverProfile) -> dict[str, Any]:
    return {
        "id": caregiver.id,
        "senior_id": caregiver.senior_id,
        "name": caregiver.name,
        "phone_number": caregiver.phone_number,
        "relationship": caregiver.relationship,
        "alert_priority": caregiver.alert_priority,
        "is_active": caregiver.is_active,
        "created_at": caregiver.created_at.isoformat() if caregiver.created_at else None,
        "updated_at": caregiver.updated_at.isoformat() if caregiver.updated_at else None,
    }


def session_to_dict(session: CheckInCallSession) -> dict[str, Any]:
    return {
        "id": session.id,
        "senior_id": session.senior_id,
        "caregiver_id": session.caregiver_id,
        "senior_name": session.senior_name,
        "senior_phone_number": session.senior_phone_number,
        "caregiver_name": session.caregiver_name,
        "caregiver_phone_number": session.caregiver_phone_number,
        "senior_call_sid": session.senior_call_sid,
        "status": session.status,
        "duration_seconds": session.duration_seconds,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


class ProfileService:
    def create_senior(
        self,
        name: str,
        phone_number: str,
        preferred_language: str = "en-US",
        notes: str | None = None,
    ) -> dict[str, Any]:
        with SessionLocal() as db:
            senior = SeniorProfile(
                name=name,
                phone_number=phone_number,
                preferred_language=preferred_language,
                notes=notes,
                is_active=True,
            )

            db.add(senior)
            db.commit()
            db.refresh(senior)

            return senior_to_dict(senior)

    def list_seniors(self) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            seniors = (
                db.query(SeniorProfile)
                .order_by(SeniorProfile.created_at.desc())
                .all()
            )

            return [senior_to_dict(senior) for senior in seniors]

    def get_senior(self, senior_id: int) -> dict[str, Any] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            return senior_to_dict(senior)

    def create_caregiver(
        self,
        senior_id: int,
        name: str,
        phone_number: str,
        relationship: str | None = None,
        alert_priority: int = 1,
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            caregiver = CaregiverProfile(
                senior_id=senior_id,
                name=name,
                phone_number=phone_number,
                relationship=relationship,
                alert_priority=alert_priority,
                is_active=True,
            )

            db.add(caregiver)
            db.commit()
            db.refresh(caregiver)

            return caregiver_to_dict(caregiver)

    def list_caregivers_for_senior(
        self,
        senior_id: int,
    ) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            caregivers = (
                db.query(CaregiverProfile)
                .filter(CaregiverProfile.senior_id == senior_id)
                .order_by(CaregiverProfile.alert_priority.asc())
                .all()
            )

            return [caregiver_to_dict(caregiver) for caregiver in caregivers]

    def get_primary_caregiver_for_senior(
        self,
        senior_id: int,
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            caregiver = (
                db.query(CaregiverProfile)
                .filter(CaregiverProfile.senior_id == senior_id)
                .filter(CaregiverProfile.is_active.is_(True))
                .order_by(CaregiverProfile.alert_priority.asc())
                .first()
            )

            if not caregiver:
                return None

            return caregiver_to_dict(caregiver)

    def create_check_in_call_session(
        self,
        senior: dict[str, Any],
        caregiver: dict[str, Any] | None,
        senior_call_sid: str,
    ) -> dict[str, Any]:
        with SessionLocal() as db:
            session = CheckInCallSession(
                senior_id=senior["id"],
                caregiver_id=caregiver["id"] if caregiver else None,
                senior_name=senior["name"],
                senior_phone_number=senior["phone_number"],
                caregiver_name=caregiver["name"] if caregiver else None,
                caregiver_phone_number=caregiver["phone_number"] if caregiver else None,
                senior_call_sid=senior_call_sid,
                status="call_started",
            )

            db.add(session)
            db.commit()
            db.refresh(session)

            return session_to_dict(session)

    def get_call_session_by_call_sid(
        self,
        senior_call_sid: str | None,
    ) -> dict[str, Any] | None:
        if not senior_call_sid:
            return None

        with SessionLocal() as db:
            session = (
                db.query(CheckInCallSession)
                .filter(CheckInCallSession.senior_call_sid == senior_call_sid)
                .first()
            )

            if not session:
                return None

            return session_to_dict(session)

    def get_alert_context_for_senior(
        self,
        senior_id: int,
    ) -> dict[str, Any] | None:
        senior = self.get_senior(senior_id)

        if not senior:
            return None

        caregiver = self.get_primary_caregiver_for_senior(senior_id)

        return {
            "senior": senior,
            "caregiver": caregiver,
        }

    def get_alert_context_for_call_sid(
        self,
        senior_call_sid: str | None,
    ) -> dict[str, Any] | None:
        session = self.get_call_session_by_call_sid(senior_call_sid)

        if not session:
            return None

        senior = {
            "id": session["senior_id"],
            "name": session["senior_name"],
            "phone_number": session["senior_phone_number"],
        }

        caregiver = None

        if session.get("caregiver_id"):
            caregiver = {
                "id": session["caregiver_id"],
                "name": session["caregiver_name"],
                "phone_number": session["caregiver_phone_number"],
            }

        return {
            "senior": senior,
            "caregiver": caregiver,
            "session": session,
        }

    def update_call_session_status(
        self,
        senior_call_sid: str | None,
        status: str | None,
        duration_seconds: str | None,
    ) -> None:
        if not senior_call_sid:
            return

        duration = _safe_int(duration_seconds)

        with SessionLocal() as db:
            session = (
                db.query(CheckInCallSession)
                .filter(CheckInCallSession.senior_call_sid == senior_call_sid)
                .first()
            )

            if not session:
                return

            if status:
                session.status = status

            if duration is not None:
                session.duration_seconds = duration

            db.commit()

    def list_recent_call_sessions(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            rows = (
                db.query(CheckInCallSession)
                .order_by(CheckInCallSession.created_at.desc())
                .limit(limit)
                .all()
            )

            return [session_to_dict(row) for row in rows]


profile_service = ProfileService()