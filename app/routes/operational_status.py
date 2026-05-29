from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.operational_status_service import operational_status_service
from app.services.profile_service import profile_service
from app.services.support_network_service import support_network_service

router = APIRouter(tags=["Operational Status"])


@router.get("/seniors/{senior_id}/operational-status")
def get_senior_operational_status(senior_id: int):
    senior = profile_service.get_senior(senior_id)

    if not senior:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    network = support_network_service.get_support_network(senior_id)
    contacts = network.get("support_contacts", []) if network else []

    return {
        "senior": senior,
        "status": operational_status_service.get_status_for_senior(
            senior=senior,
            has_support_contact=bool(contacts),
        ),
    }


@router.get("/operational-status")
def list_operational_statuses():
    items = []

    for senior in profile_service.list_seniors():
        network = support_network_service.get_support_network(int(senior["id"]))
        contacts = network.get("support_contacts", []) if network else []

        items.append(
            {
                "senior": senior,
                "status": operational_status_service.get_status_for_senior(
                    senior=senior,
                    has_support_contact=bool(contacts),
                ),
            }
        )

    return {
        "items": items,
    }