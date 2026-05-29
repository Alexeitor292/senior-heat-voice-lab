from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.services.profile_service import profile_service
from app.services.twilio_service import twilio_service
from app.services.baseline_comparison_service import baseline_comparison_service
from app.services.voice_baseline_service import (
    DEFAULT_BASELINE_PROMPT,
    voice_baseline_service,
)

router = APIRouter(tags=["Voice Baselines"])


class BaselineStartRequest(BaseModel):
    prompt_text: str | None = None
    notes: str | None = None


@router.post("/seniors/{senior_id}/baseline/start")
def start_baseline_collection_call(
    senior_id: int,
    payload: BaselineStartRequest | None = None,
):
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

    prompt_text = (
        payload.prompt_text
        if payload and payload.prompt_text
        else DEFAULT_BASELINE_PROMPT
    )

    notes = payload.notes if payload else None

    call = twilio_service.start_senior_baseline_call(
        senior_id=senior["id"],
        senior_phone_number=senior["phone_number"],
    )

    baseline = voice_baseline_service.create_pending_baseline_sample(
        senior_id=senior["id"],
        baseline_call_sid=call.sid,
        prompt_text=prompt_text,
        notes=notes,
    )

    return {
        "message": "Baseline voice collection call started.",
        "senior": senior,
        "call_sid": call.sid,
        "baseline": baseline,
        "next_step": "Answer the phone and read the baseline phrase clearly.",
    }


@router.get("/seniors/{senior_id}/baselines")
def list_baselines_for_senior(senior_id: int):
    senior = profile_service.get_senior(senior_id)

    if not senior:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "senior": senior,
        "items": voice_baseline_service.list_baselines_for_senior(senior_id),
    }


@router.get("/debug/baselines")
def list_recent_baselines(limit: int = 10):
    return {
        "items": voice_baseline_service.list_recent_baselines(limit=limit)
    }

@router.get("/seniors/{senior_id}/baseline-comparisons")
def list_baseline_comparisons_for_senior(senior_id: int):
    senior = profile_service.get_senior(senior_id)

    if not senior:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "senior": senior,
        "items": baseline_comparison_service.list_comparisons_for_senior(senior_id),
    }