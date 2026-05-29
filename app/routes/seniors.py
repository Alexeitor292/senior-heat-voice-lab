from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.services.profile_service import profile_service
from app.services.twilio_service import twilio_service

router = APIRouter(prefix="/seniors", tags=["Seniors"])


class SeniorCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    phone_number: str = Field(..., min_length=8)
    preferred_language: str = "en-US"
    notes: str | None = None


class CaregiverCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    phone_number: str = Field(..., min_length=8)
    relationship: str | None = None
    alert_priority: int = 1


@router.post("")
def create_senior(payload: SeniorCreateRequest):
    senior = profile_service.create_senior(
        name=payload.name,
        phone_number=payload.phone_number,
        preferred_language=payload.preferred_language,
        notes=payload.notes,
    )

    return {
        "message": "Senior profile created.",
        "senior": senior,
    }


@router.get("")
def list_seniors():
    return {
        "items": profile_service.list_seniors()
    }


@router.get("/{senior_id}")
def get_senior(senior_id: int):
    senior = profile_service.get_senior(senior_id)

    if not senior:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    caregivers = profile_service.list_caregivers_for_senior(senior_id)

    return {
        "senior": senior,
        "caregivers": caregivers,
    }


@router.post("/{senior_id}/caregivers")
def create_caregiver(
    senior_id: int,
    payload: CaregiverCreateRequest,
):
    caregiver = profile_service.create_caregiver(
        senior_id=senior_id,
        name=payload.name,
        phone_number=payload.phone_number,
        relationship=payload.relationship,
        alert_priority=payload.alert_priority,
    )

    if not caregiver:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "message": "Caregiver profile created.",
        "caregiver": caregiver,
    }


@router.get("/{senior_id}/caregivers")
def list_caregivers(senior_id: int):
    senior = profile_service.get_senior(senior_id)

    if not senior:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    caregivers = profile_service.list_caregivers_for_senior(senior_id)

    return {
        "senior_id": senior_id,
        "items": caregivers,
    }


@router.post("/{senior_id}/start-check-in")
def start_profile_based_check_in(senior_id: int):
    senior = profile_service.get_senior(senior_id)

    if not senior:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    if not senior["is_active"]:
        raise HTTPException(
            status_code=400,
            detail="Senior profile is inactive.",
        )

    caregiver = profile_service.get_primary_caregiver_for_senior(senior_id)

    call = twilio_service.start_senior_speech_check_call(
        senior_id=senior["id"],
        senior_phone_number=senior["phone_number"],
    )

    session = profile_service.create_check_in_call_session(
        senior=senior,
        caregiver=caregiver,
        senior_call_sid=call.sid,
    )

    return {
        "message": "Profile-based speech check-in started.",
        "senior": senior,
        "primary_caregiver": caregiver,
        "call_sid": call.sid,
        "session": session,
        "next_step": "Answer the senior phone and speak the check-in response.",
    }