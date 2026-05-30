from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.checkin_review_service import checkin_review_service

router = APIRouter(tags=["Check-Ins"])


@router.get("/check-ins/{check_in_id}/review")
def get_check_in_review(check_in_id: int):
    result = checkin_review_service.get_review(check_in_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Check-in not found.",
        )

    return result