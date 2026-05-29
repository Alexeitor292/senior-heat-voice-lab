from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.support_network_service import support_network_service

router = APIRouter(tags=["Support Network"])


class EscalationPlanRequest(BaseModel):
    living_situation: str = "Unknown"
    support_mode: str = "Self-managed"
    allow_operator_review: bool = True
    allow_wellness_check: bool = True
    allow_emergency_escalation: bool = False
    notes: str | None = None


class SupportContactCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    phone_number: str = Field(..., min_length=8)
    relationship: str | None = None
    contact_type: str = "family"
    priority: int = 1
    can_receive_alerts: bool = True
    is_emergency_contact: bool = False
    notes: str | None = None


class SupportContactUpdateRequest(BaseModel):
    name: str | None = None
    phone_number: str | None = None
    relationship: str | None = None
    contact_type: str | None = None
    priority: int | None = None
    can_receive_alerts: bool | None = None
    is_emergency_contact: bool | None = None
    is_active: bool | None = None
    notes: str | None = None


class EscalationStepCreateRequest(BaseModel):
    step_order: int = 1
    trigger_level: str = "moderate"
    action_type: str = "operator_review"
    target_contact_id: int | None = None
    instructions: str | None = None


@router.get("/seniors/{senior_id}/support-network")
def get_support_network(senior_id: int):
    result = support_network_service.get_support_network(senior_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return result


@router.put("/seniors/{senior_id}/escalation-plan")
def upsert_escalation_plan(
    senior_id: int,
    payload: EscalationPlanRequest,
):
    result = support_network_service.upsert_escalation_plan(
        senior_id=senior_id,
        payload=payload.model_dump(),
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "message": "Escalation plan saved.",
        "plan": result,
    }


@router.post("/seniors/{senior_id}/support-contacts")
def create_support_contact(
    senior_id: int,
    payload: SupportContactCreateRequest,
):
    result = support_network_service.create_support_contact(
        senior_id=senior_id,
        payload=payload.model_dump(),
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "message": "Support contact created.",
        "support_contact": result,
    }


@router.patch("/support-contacts/{contact_id}")
def update_support_contact(
    contact_id: int,
    payload: SupportContactUpdateRequest,
):
    result = support_network_service.update_support_contact(
        contact_id=contact_id,
        payload=payload.model_dump(exclude_unset=True),
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Support contact not found.",
        )

    return {
        "message": "Support contact updated.",
        "support_contact": result,
    }


@router.delete("/support-contacts/{contact_id}")
def deactivate_support_contact(contact_id: int):
    result = support_network_service.deactivate_support_contact(contact_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Support contact not found.",
        )

    return {
        "message": "Support contact deactivated.",
        "support_contact": result,
    }


@router.post("/seniors/{senior_id}/escalation-steps")
def create_escalation_step(
    senior_id: int,
    payload: EscalationStepCreateRequest,
):
    result = support_network_service.create_escalation_step(
        senior_id=senior_id,
        payload=payload.model_dump(),
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "message": "Escalation step created.",
        "step": result,
    }