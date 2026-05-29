from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.services.profile_service import profile_service
from app.services.schedule_service import schedule_service

router = APIRouter(tags=["Schedules"])


class ScheduleCreateRequest(BaseModel):
    name: str = "Default heat check-in schedule"
    time_of_day: str = Field(..., description="24-hour time in HH:MM format")
    timezone: str = "America/Los_Angeles"
    days_of_week: list[int] = Field(
        default_factory=lambda: [0, 1, 2, 3, 4, 5, 6],
        description="Monday=0, Tuesday=1, ..., Sunday=6",
    )
    enabled: bool = True


class ScheduleEnabledRequest(BaseModel):
    enabled: bool


@router.post("/seniors/{senior_id}/schedules")
def create_schedule_for_senior(
    senior_id: int,
    payload: ScheduleCreateRequest,
):
    try:
        schedule = schedule_service.create_schedule(
            senior_id=senior_id,
            name=payload.name,
            time_of_day=payload.time_of_day,
            timezone_name=payload.timezone,
            days_of_week=payload.days_of_week,
            enabled=payload.enabled,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if not schedule:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "message": "Check-in schedule created.",
        "schedule": schedule,
    }


@router.get("/seniors/{senior_id}/schedules")
def list_schedules_for_senior(senior_id: int):
    senior = profile_service.get_senior(senior_id)

    if not senior:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return {
        "senior": senior,
        "items": schedule_service.list_schedules(senior_id=senior_id),
    }


@router.get("/schedules")
def list_all_schedules():
    return {
        "items": schedule_service.list_schedules()
    }


@router.get("/schedules/due")
def list_due_schedules():
    return {
        "items": schedule_service.list_due_schedules()
    }


@router.patch("/schedules/{schedule_id}/enabled")
def set_schedule_enabled(
    schedule_id: int,
    payload: ScheduleEnabledRequest,
):
    schedule = schedule_service.set_schedule_enabled(
        schedule_id=schedule_id,
        enabled=payload.enabled,
    )

    if not schedule:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found.",
        )

    return {
        "message": "Schedule updated.",
        "schedule": schedule,
    }


@router.post("/scheduler/run-due-checks")
def run_due_checks():
    return schedule_service.run_due_check_ins()