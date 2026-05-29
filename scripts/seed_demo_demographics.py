from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.db.database import SessionLocal, init_db
from app.db.models import SeniorDemographics, SeniorProfile


DEMO_DEMOGRAPHICS_BY_NAME = {
    "Juan Test Senior": {
        "age_years": 78,
        "gender": "Male",
        "pronouns": "he/him",
        "primary_language": "en-US",
        "notes": "Local test senior demographics.",
    },
    "Eleanor Jennings": {
        "age_years": 79,
        "gender": "Female",
        "pronouns": "she/her",
        "primary_language": "en-US",
        "notes": "Lives alone. High heat sensitivity.",
    },
    "Robert Martinez": {
        "age_years": 82,
        "gender": "Male",
        "pronouns": "he/him",
        "primary_language": "en-US",
        "notes": "Family-supported senior.",
    },
    "Lillian Carter": {
        "age_years": 86,
        "gender": "Female",
        "pronouns": "she/her",
        "primary_language": "en-US",
        "notes": "Self-managed senior.",
    },
    "James Wilson": {
        "age_years": 74,
        "gender": "Male",
        "pronouns": "he/him",
        "primary_language": "en-US",
        "notes": "Facility-supported senior.",
    },
}


def upsert_demographics(db, senior: SeniorProfile, values: dict) -> None:
    row = (
        db.query(SeniorDemographics)
        .filter(SeniorDemographics.senior_id == senior.id)
        .first()
    )

    if not row:
        row = SeniorDemographics(senior_id=senior.id)
        db.add(row)

    row.date_of_birth = values.get("date_of_birth")
    row.age_years = values.get("age_years")
    row.gender = values.get("gender")
    row.pronouns = values.get("pronouns")
    row.primary_language = values.get("primary_language")
    row.notes = values.get("notes")


def main():
    init_db()

    with SessionLocal() as db:
        seniors = db.query(SeniorProfile).all()

        if not seniors:
            print("No seniors found. Create or seed seniors first.")
            return

        updated = 0

        for senior in seniors:
            values = DEMO_DEMOGRAPHICS_BY_NAME.get(senior.name)

            if not values:
                continue

            upsert_demographics(db, senior, values)
            updated += 1

        db.commit()

    print(f"Demo demographics seeded for {updated} senior(s).")


if __name__ == "__main__":
    main()