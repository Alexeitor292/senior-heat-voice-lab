from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.timeline_service import timeline_service

router = APIRouter(tags=["Timeline"])


@router.get("/seniors/{senior_id}/timeline")
def get_senior_timeline(
    senior_id: int,
    limit: int = Query(default=20, ge=1, le=100),
):
    result = timeline_service.get_timeline_for_senior(
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