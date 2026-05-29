from __future__ import annotations

from typing import Any

from app.db.database import SessionLocal
from app.db.models import (
    CaregiverProfile,
    EscalationPlan,
    EscalationStep,
    SeniorProfile,
    SupportContact,
)


def _iso(value):
    return value.isoformat() if value else None


def support_contact_to_dict(row: SupportContact) -> dict[str, Any]:
    return {
        "id": row.id,
        "source": "support_contact",
        "senior_id": row.senior_id,
        "name": row.name,
        "phone_number": row.phone_number,
        "relationship": row.relationship,
        "contact_type": row.contact_type,
        "priority": row.priority,
        "can_receive_alerts": row.can_receive_alerts,
        "is_emergency_contact": row.is_emergency_contact,
        "is_active": row.is_active,
        "notes": row.notes,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def legacy_caregiver_to_support_contact_dict(row: CaregiverProfile) -> dict[str, Any]:
    return {
        "id": f"caregiver-{row.id}",
        "source": "legacy_caregiver",
        "senior_id": row.senior_id,
        "name": row.name,
        "phone_number": row.phone_number,
        "relationship": row.relationship,
        "contact_type": "caregiver",
        "priority": row.alert_priority,
        "can_receive_alerts": True,
        "is_emergency_contact": row.alert_priority == 1,
        "is_active": row.is_active,
        "notes": "Legacy caregiver record exposed as support contact.",
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def escalation_plan_to_dict(row: EscalationPlan) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "living_situation": row.living_situation,
        "support_mode": row.support_mode,
        "allow_operator_review": row.allow_operator_review,
        "allow_wellness_check": row.allow_wellness_check,
        "allow_emergency_escalation": row.allow_emergency_escalation,
        "notes": row.notes,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def escalation_step_to_dict(row: EscalationStep) -> dict[str, Any]:
    return {
        "id": row.id,
        "plan_id": row.plan_id,
        "step_order": row.step_order,
        "trigger_level": row.trigger_level,
        "action_type": row.action_type,
        "target_contact_id": row.target_contact_id,
        "instructions": row.instructions,
        "is_active": row.is_active,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


class SupportNetworkService:
    def get_support_network(self, senior_id: int) -> dict[str, Any] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            plan = (
                db.query(EscalationPlan)
                .filter(EscalationPlan.senior_id == senior_id)
                .first()
            )

            support_contacts = (
                db.query(SupportContact)
                .filter(SupportContact.senior_id == senior_id)
                .filter(SupportContact.is_active.is_(True))
                .order_by(SupportContact.priority.asc(), SupportContact.created_at.asc())
                .all()
            )

            contacts = [support_contact_to_dict(row) for row in support_contacts]

            # Compatibility bridge:
            # If no new support contacts exist yet, expose old CaregiverProfile rows
            # as support contacts for read/display purposes.
            if not contacts:
                legacy_caregivers = (
                    db.query(CaregiverProfile)
                    .filter(CaregiverProfile.senior_id == senior_id)
                    .filter(CaregiverProfile.is_active.is_(True))
                    .order_by(CaregiverProfile.alert_priority.asc())
                    .all()
                )

                contacts = [
                    legacy_caregiver_to_support_contact_dict(row)
                    for row in legacy_caregivers
                ]

            steps = []
            if plan:
                step_rows = (
                    db.query(EscalationStep)
                    .filter(EscalationStep.plan_id == plan.id)
                    .filter(EscalationStep.is_active.is_(True))
                    .order_by(EscalationStep.step_order.asc())
                    .all()
                )

                steps = [escalation_step_to_dict(row) for row in step_rows]

            return {
                "senior_id": senior_id,
                "plan": escalation_plan_to_dict(plan) if plan else None,
                "support_contacts": contacts,
                "steps": steps,
            }

    def upsert_escalation_plan(
        self,
        senior_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            plan = (
                db.query(EscalationPlan)
                .filter(EscalationPlan.senior_id == senior_id)
                .first()
            )

            if not plan:
                plan = EscalationPlan(
                    senior_id=senior_id,
                    living_situation=payload.get("living_situation") or "Unknown",
                    support_mode=payload.get("support_mode") or "Self-managed",
                    allow_operator_review=payload.get("allow_operator_review", True),
                    allow_wellness_check=payload.get("allow_wellness_check", True),
                    allow_emergency_escalation=payload.get(
                        "allow_emergency_escalation",
                        False,
                    ),
                    notes=payload.get("notes"),
                )
                db.add(plan)
            else:
                allowed_fields = {
                    "living_situation",
                    "support_mode",
                    "allow_operator_review",
                    "allow_wellness_check",
                    "allow_emergency_escalation",
                    "notes",
                }

                for field in allowed_fields:
                    if field in payload:
                        setattr(plan, field, payload[field])

            db.commit()
            db.refresh(plan)

            return escalation_plan_to_dict(plan)

    def create_support_contact(
        self,
        senior_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            contact = SupportContact(
                senior_id=senior_id,
                name=payload["name"],
                phone_number=payload["phone_number"],
                relationship=payload.get("relationship"),
                contact_type=payload.get("contact_type") or "family",
                priority=payload.get("priority", 1),
                can_receive_alerts=payload.get("can_receive_alerts", True),
                is_emergency_contact=payload.get("is_emergency_contact", False),
                notes=payload.get("notes"),
                is_active=True,
            )

            db.add(contact)
            db.commit()
            db.refresh(contact)

            return support_contact_to_dict(contact)

    def update_support_contact(
        self,
        contact_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            contact = db.get(SupportContact, contact_id)

            if not contact:
                return None

            allowed_fields = {
                "name",
                "phone_number",
                "relationship",
                "contact_type",
                "priority",
                "can_receive_alerts",
                "is_emergency_contact",
                "is_active",
                "notes",
            }

            for field in allowed_fields:
                if field in payload:
                    setattr(contact, field, payload[field])

            db.commit()
            db.refresh(contact)

            return support_contact_to_dict(contact)

    def deactivate_support_contact(self, contact_id: int) -> dict[str, Any] | None:
        with SessionLocal() as db:
            contact = db.get(SupportContact, contact_id)

            if not contact:
                return None

            contact.is_active = False
            db.commit()
            db.refresh(contact)

            return support_contact_to_dict(contact)

    def create_escalation_step(
        self,
        senior_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            plan = (
                db.query(EscalationPlan)
                .filter(EscalationPlan.senior_id == senior_id)
                .first()
            )

            if not plan:
                plan = EscalationPlan(
                    senior_id=senior_id,
                    living_situation="Unknown",
                    support_mode="Self-managed",
                    allow_operator_review=True,
                    allow_wellness_check=True,
                    allow_emergency_escalation=False,
                )
                db.add(plan)
                db.flush()

            step = EscalationStep(
                plan_id=plan.id,
                step_order=payload.get("step_order", 1),
                trigger_level=payload.get("trigger_level") or "moderate",
                action_type=payload.get("action_type") or "operator_review",
                target_contact_id=payload.get("target_contact_id"),
                instructions=payload.get("instructions"),
                is_active=True,
            )

            db.add(step)
            db.commit()
            db.refresh(step)

            return escalation_step_to_dict(step)


support_network_service = SupportNetworkService()