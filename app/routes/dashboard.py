from fastapi import APIRouter, HTTPException, Query

from app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary():
    return dashboard_service.get_summary()


@router.get("/seniors")
def list_dashboard_seniors():
    return {
        "items": dashboard_service.list_senior_cards()
    }


@router.get("/seniors/{senior_id}")
def get_dashboard_senior(senior_id: int):
    result = dashboard_service.get_senior_dashboard(senior_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return result


@router.get("/seniors/{senior_id}/timeline")
def get_senior_timeline(
    senior_id: int,
    limit: int = Query(default=50, ge=1, le=200),
):
    result = dashboard_service.list_timeline_for_senior(
        senior_id=senior_id,
        limit=limit,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Senior profile not found.",
        )

    return result


@router.get("/check-ins")
def list_dashboard_check_ins(
    limit: int = Query(default=25, ge=1, le=200),
):
    return {
        "items": dashboard_service.list_check_ins(limit=limit)
    }


@router.get("/alerts")
def list_dashboard_alerts(
    limit: int = Query(default=25, ge=1, le=200),
):
    return {
        "items": dashboard_service.list_alerts(limit=limit)
    }