from __future__ import annotations

from datetime import date
from typing import Any

from app.db.database import SessionLocal
from app.db.models import SeniorDemographics, SeniorProfile


def _iso(value):
    return value.isoformat() if value else None


def _calculate_age_from_dob(date_of_birth: str | None) -> int | None:
    if not date_of_birth:
        return None

    try:
        year, month, day = [int(part) for part in date_of_birth.split("-")]
        born = date(year, month, day)
    except (ValueError, TypeError):
        return None

    today = date.today()
    age = today.year - born.year

    if (today.month, today.day) < (born.month, born.day):
        age -= 1

    return age


def demographics_to_dict(row: SeniorDemographics) -> dict[str, Any]:
    computed_age = _calculate_age_from_dob(row.date_of_birth)

    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "date_of_birth": row.date_of_birth,
        "age_years": computed_age if computed_age is not None else row.age_years,
        "gender": row.gender,
        "pronouns": row.pronouns,
        "primary_language": row.primary_language,
        "notes": row.notes,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


class DemographicsService:
    def get_demographics(self, senior_id: int) -> dict[str, Any] | None:
        with SessionLocal() as db:
            row = (
                db.query(SeniorDemographics)
                .filter(SeniorDemographics.senior_id == senior_id)
                .first()
            )

            if not row:
                return None

            return demographics_to_dict(row)

    def upsert_demographics(
        self,
        senior_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            row = (
                db.query(SeniorDemographics)
                .filter(SeniorDemographics.senior_id == senior_id)
                .first()
            )

            if not row:
                row = SeniorDemographics(senior_id=senior_id)
                db.add(row)

            allowed_fields = {
                "date_of_birth",
                "age_years",
                "gender",
                "pronouns",
                "primary_language",
                "notes",
            }

            for field in allowed_fields:
                if field in payload:
                    setattr(row, field, payload[field])

            db.commit()
            db.refresh(row)

            return demographics_to_dict(row)


demographics_service = DemographicsService()