from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.services.heat_risk_service import heat_risk_service
from app.services.profile_service import profile_service

router = APIRouter(tags=["HeatRisk"])


class SeniorHeatSettingsRequest(BaseModel):
    enabled: bool = True

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    city: str | None = None
    state: str | None = None
    zip_code: str | None = None

    timezone: str = "America/Los_Angeles"

    # 0 = little/no risk, 1 = minor, 2 = moderate, 3 = major, 4 = extreme
    trigger_threshold: int = Field(default=2, ge=0, le=4)


@router.put("/seniors/{senior_id}/heat-settings")
def upsert_heat_settings(
    senior_id: int,
    payload: SeniorHeatSettingsRequest,
):
    try:
        result = heat_risk_service.upsert_heat_settings(
            senior_id=senior_id,
            enabled=payload.enabled,
            latitude=payload.latitude,
            longitude=payload.longitude,
            city=payload.city,
            state=payload.state,
            zip_code=payload.zip_code,
            timezone_name=payload.timezone,
            trigger_threshold=payload.trigger_threshold,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "message": "Senior HeatRisk settings saved.",
        "heat_settings": result,
    }


@router.get("/seniors/{senior_id}/heat-settings")
def get_heat_settings(senior_id: int):
    senior = profile_service.get_senior(senior_id)

    if not senior:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    settings = heat_risk_service.get_heat_settings(senior_id)

    if not settings:
        raise HTTPException(
            status_code=404,
            detail="HeatRisk settings not found for senior.",
        )

    return {
        "senior": senior,
        "heat_settings": settings,
    }


@router.get("/seniors/{senior_id}/heat-risk")
def get_heat_risk_for_senior(senior_id: int):
    senior = profile_service.get_senior(senior_id)

    if not senior:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    try:
        result = heat_risk_service.get_current_heat_risk_for_senior(senior_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "senior": senior,
        "result": result,
    }


@router.get("/heat-settings")
def list_heat_settings():
    return {
        "items": heat_risk_service.list_heat_settings()
    }


@router.post("/scheduler/run-heat-risk-checks")
def run_heat_risk_checks():
    return heat_risk_service.run_heat_risk_checks()