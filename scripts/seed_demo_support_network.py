from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.db.database import SessionLocal, init_db
from app.db.models import (
    EscalationPlan,
    EscalationStep,
    SeniorHeatSettings,
    SeniorProfile,
    SupportContact,
)


DEMO_SENIORS = [
    {
        "name": "Eleanor Jennings",
        "phone_number": "+15550100101",
        "preferred_language": "en-US",
        "notes": "Lives alone. High heat sensitivity. No support contact listed.",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85016",
        "latitude": 33.45,
        "longitude": -112.07,
        "timezone": "America/Phoenix",
        "living_situation": "Lives alone",
        "support_mode": "Operator monitored",
        "plan_notes": "No support contact listed. Route high-risk cases to operator review and wellness check.",
        "contacts": [],
        "steps": [
            {
                "step_order": 1,
                "trigger_level": "moderate",
                "action_type": "retry_senior",
                "instructions": "Retry senior by phone within 20 minutes.",
            },
            {
                "step_order": 2,
                "trigger_level": "high",
                "action_type": "operator_review",
                "instructions": "Operator reviews transcript, symptoms, and heat risk.",
            },
            {
                "step_order": 3,
                "trigger_level": "urgent",
                "action_type": "dispatch_wellness_check",
                "instructions": "Recommend wellness check if no response or severe symptoms.",
            },
        ],
    },
    {
        "name": "Robert Martinez",
        "phone_number": "+15550100102",
        "preferred_language": "en-US",
        "notes": "Family-supported senior with daughter as primary support.",
        "city": "San Antonio",
        "state": "TX",
        "zip_code": "78205",
        "latitude": 29.42,
        "longitude": -98.49,
        "timezone": "America/Chicago",
        "living_situation": "Lives with family",
        "support_mode": "Family supported",
        "plan_notes": "Contact family first. Escalate to operator if no support contact responds.",
        "contacts": [
            {
                "name": "Maria Martinez",
                "phone_number": "+15550101102",
                "relationship": "Daughter",
                "contact_type": "family",
                "priority": 1,
                "can_receive_alerts": True,
                "is_emergency_contact": True,
            },
            {
                "name": "Luis Ortega",
                "phone_number": "+15550102102",
                "relationship": "Neighbor",
                "contact_type": "neighbor",
                "priority": 2,
                "can_receive_alerts": True,
                "is_emergency_contact": False,
            },
        ],
        "steps": [
            {
                "step_order": 1,
                "trigger_level": "moderate",
                "action_type": "call_support_contact",
                "instructions": "Call daughter first.",
            },
            {
                "step_order": 2,
                "trigger_level": "high",
                "action_type": "call_support_contact",
                "instructions": "Call neighbor if daughter does not respond.",
            },
            {
                "step_order": 3,
                "trigger_level": "urgent",
                "action_type": "operator_review",
                "instructions": "Operator decides whether wellness check is needed.",
            },
        ],
    },
    {
        "name": "Lillian Carter",
        "phone_number": "+15550100103",
        "preferred_language": "en-US",
        "notes": "Self-managed senior with one emergency contact.",
        "city": "New Orleans",
        "state": "LA",
        "zip_code": "70130",
        "latitude": 29.95,
        "longitude": -90.07,
        "timezone": "America/Chicago",
        "living_situation": "Lives alone",
        "support_mode": "Self-managed",
        "plan_notes": "Retry senior first. If no response, notify emergency contact.",
        "contacts": [
            {
                "name": "Frank Carter",
                "phone_number": "+15550101103",
                "relationship": "Brother",
                "contact_type": "family",
                "priority": 1,
                "can_receive_alerts": True,
                "is_emergency_contact": True,
            },
        ],
        "steps": [
            {
                "step_order": 1,
                "trigger_level": "moderate",
                "action_type": "retry_senior",
                "instructions": "Retry senior before contacting support.",
            },
            {
                "step_order": 2,
                "trigger_level": "high",
                "action_type": "call_support_contact",
                "instructions": "Call emergency contact if senior does not respond.",
            },
        ],
    },
    {
        "name": "James Wilson",
        "phone_number": "+15550100104",
        "preferred_language": "en-US",
        "notes": "Senior community resident.",
        "city": "Miami",
        "state": "FL",
        "zip_code": "33139",
        "latitude": 25.77,
        "longitude": -80.19,
        "timezone": "America/New_York",
        "living_situation": "Senior community",
        "support_mode": "Facility supported",
        "plan_notes": "Notify facility front desk for urgent cases.",
        "contacts": [
            {
                "name": "Bayview Senior Community Front Desk",
                "phone_number": "+15550101104",
                "relationship": "Facility front desk",
                "contact_type": "facility_staff",
                "priority": 1,
                "can_receive_alerts": True,
                "is_emergency_contact": False,
            },
        ],
        "steps": [
            {
                "step_order": 1,
                "trigger_level": "moderate",
                "action_type": "call_support_contact",
                "instructions": "Call facility front desk.",
            },
            {
                "step_order": 2,
                "trigger_level": "urgent",
                "action_type": "dispatch_wellness_check",
                "instructions": "Facility staff should physically check on resident.",
            },
        ],
    },
]


def get_or_create_senior(db, senior_data: dict) -> SeniorProfile:
    senior = (
        db.query(SeniorProfile)
        .filter(SeniorProfile.name == senior_data["name"])
        .first()
    )

    if senior:
        return senior

    senior = SeniorProfile(
        name=senior_data["name"],
        phone_number=senior_data["phone_number"],
        preferred_language=senior_data["preferred_language"],
        notes=senior_data["notes"],
        is_active=True,
    )

    db.add(senior)
    db.flush()

    return senior


def upsert_heat_settings(db, senior: SeniorProfile, senior_data: dict) -> None:
    settings = (
        db.query(SeniorHeatSettings)
        .filter(SeniorHeatSettings.senior_id == senior.id)
        .first()
    )

    if not settings:
        settings = SeniorHeatSettings(senior_id=senior.id)
        db.add(settings)

    settings.enabled = True
    settings.city = senior_data["city"]
    settings.state = senior_data["state"]
    settings.zip_code = senior_data["zip_code"]
    settings.latitude = senior_data["latitude"]
    settings.longitude = senior_data["longitude"]
    settings.timezone = senior_data["timezone"]
    settings.trigger_threshold = 2


def upsert_escalation_plan(db, senior: SeniorProfile, senior_data: dict) -> EscalationPlan:
    plan = (
        db.query(EscalationPlan)
        .filter(EscalationPlan.senior_id == senior.id)
        .first()
    )

    if not plan:
        plan = EscalationPlan(senior_id=senior.id)
        db.add(plan)
        db.flush()

    plan.living_situation = senior_data["living_situation"]
    plan.support_mode = senior_data["support_mode"]
    plan.allow_operator_review = True
    plan.allow_wellness_check = True
    plan.allow_emergency_escalation = False
    plan.notes = senior_data["plan_notes"]

    return plan


def replace_contacts(db, senior: SeniorProfile, senior_data: dict) -> None:
    existing_contacts = (
        db.query(SupportContact)
        .filter(SupportContact.senior_id == senior.id)
        .all()
    )

    for contact in existing_contacts:
        db.delete(contact)

    db.flush()

    for contact_data in senior_data["contacts"]:
        db.add(
            SupportContact(
                senior_id=senior.id,
                name=contact_data["name"],
                phone_number=contact_data["phone_number"],
                relationship=contact_data["relationship"],
                contact_type=contact_data["contact_type"],
                priority=contact_data["priority"],
                can_receive_alerts=contact_data["can_receive_alerts"],
                is_emergency_contact=contact_data["is_emergency_contact"],
                is_active=True,
            )
        )


def replace_steps(db, plan: EscalationPlan, senior_data: dict) -> None:
    existing_steps = (
        db.query(EscalationStep)
        .filter(EscalationStep.plan_id == plan.id)
        .all()
    )

    for step in existing_steps:
        db.delete(step)

    db.flush()

    for step_data in senior_data["steps"]:
        db.add(
            EscalationStep(
                plan_id=plan.id,
                step_order=step_data["step_order"],
                trigger_level=step_data["trigger_level"],
                action_type=step_data["action_type"],
                instructions=step_data["instructions"],
                is_active=True,
            )
        )


def main():
    init_db()

    with SessionLocal() as db:
        for senior_data in DEMO_SENIORS:
            senior = get_or_create_senior(db, senior_data)
            upsert_heat_settings(db, senior, senior_data)
            plan = upsert_escalation_plan(db, senior, senior_data)
            replace_contacts(db, senior, senior_data)
            replace_steps(db, plan, senior_data)

        db.commit()

    print("Demo support-network data seeded.")


if __name__ == "__main__":
    main()