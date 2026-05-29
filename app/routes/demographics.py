from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.demographics_service import demographics_service

router = APIRouter(tags=["Demographics"])


class DemographicsRequest(BaseModel):
    date_of_birth: str | None = Field(
        default=None,
        description="YYYY-MM-DD format.",
    )
    age_years: int | None = Field(default=None, ge=0, le=130)
    gender: str | None = None
    pronouns: str | None = None
    primary_language: str | None = None
    notes: str | None = None


@router.get("/seniors/{senior_id}/demographics")
def get_demographics(senior_id: int):
    result = demographics_service.get_demographics(senior_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Demographics not found for senior.",
        )

    return {
        "senior_id": senior_id,
        "demographics": result,
    }


@router.put("/seniors/{senior_id}/demographics")
def upsert_demographics(
    senior_id: int,
    payload: DemographicsRequest,
):
    result = demographics_service.upsert_demographics(
        senior_id=senior_id,
        payload=payload.model_dump(exclude_unset=True),
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "message": "Senior demographics saved.",
        "demographics": result,
    }