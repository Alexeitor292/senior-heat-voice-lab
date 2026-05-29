from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.operator_action_service import operator_action_service

router = APIRouter(tags=["Operator Actions"])


class OperatorActionCreateRequest(BaseModel):
    action_type: str = Field(..., min_length=1)
    status: str = "requested"
    reason: str | None = None
    note: str | None = None
    target_contact_id: int | None = None
    created_by: str | None = "operator"


class OperatorActionUpdateRequest(BaseModel):
    status: str | None = None
    reason: str | None = None
    note: str | None = None
    target_contact_id: int | None = None
    created_by: str | None = None


@router.post("/seniors/{senior_id}/operator-actions")
def create_operator_action(
    senior_id: int,
    payload: OperatorActionCreateRequest,
):
    result = operator_action_service.create_action(
        senior_id=senior_id,
        payload=payload.model_dump(),
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "message": "Operator action created.",
        "action": result,
    }


@router.get("/seniors/{senior_id}/operator-actions")
def list_operator_actions(
    senior_id: int,
    limit: int = Query(default=50, ge=1, le=100),
):
    result = operator_action_service.list_actions_for_senior(
        senior_id=senior_id,
        limit=limit,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "senior_id": senior_id,
        "items": result,
    }

@router.get("/operator-actions")
def list_operator_actions_filtered(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=250),
):
    return {
        "items": operator_action_service.list_actions(
            status=status,
            limit=limit,
        ),
    }

@router.get("/operator-actions/pending")
def list_pending_operator_actions(
    limit: int = Query(default=50, ge=1, le=100),
):
    return {
        "items": operator_action_service.list_pending_actions(limit=limit),
    }

@router.patch("/operator-actions/{action_id}")
def update_operator_action(
    action_id: int,
    payload: OperatorActionUpdateRequest,
):
    result = operator_action_service.update_action(
        action_id=action_id,
        payload=payload.model_dump(exclude_unset=True),
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Operator action not found.",
        )

    return {
        "message": "Operator action updated.",
        "action": result,
    }