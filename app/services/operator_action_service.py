from __future__ import annotations

from typing import Any

from app.db.database import SessionLocal
from app.db.models import OperatorAction, SeniorProfile


PENDING_ACTION_STATUSES = {"requested", "in_progress"}


def _iso(value):
    return value.isoformat() if value else None


def operator_action_to_dict(
    row: OperatorAction,
    senior: SeniorProfile | None = None,
) -> dict[str, Any]:
    result = {
        "id": row.id,
        "senior_id": row.senior_id,
        "action_type": row.action_type,
        "status": row.status,
        "reason": row.reason,
        "note": row.note,
        "target_contact_id": row.target_contact_id,
        "created_by": row.created_by,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }

    if senior is not None:
        result["senior_name"] = senior.name
        result["senior_phone_number"] = senior.phone_number

    return result


class OperatorActionService:
    def create_action(
        self,
        senior_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            action = OperatorAction(
                senior_id=senior_id,
                action_type=payload["action_type"],
                status=payload.get("status") or "requested",
                reason=payload.get("reason"),
                note=payload.get("note"),
                target_contact_id=payload.get("target_contact_id"),
                created_by=payload.get("created_by") or "operator",
            )

            db.add(action)
            db.commit()
            db.refresh(action)

            return operator_action_to_dict(action, senior)

    def list_actions_for_senior(
        self,
        senior_id: int,
        limit: int = 50,
    ) -> list[dict[str, Any]] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            rows = (
                db.query(OperatorAction)
                .filter(OperatorAction.senior_id == senior_id)
                .order_by(OperatorAction.created_at.desc())
                .limit(limit)
                .all()
            )

            return [operator_action_to_dict(row, senior) for row in rows]

    def list_pending_actions(
        self,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            rows = (
                db.query(OperatorAction, SeniorProfile)
                .join(SeniorProfile, OperatorAction.senior_id == SeniorProfile.id)
                .filter(OperatorAction.status.in_(PENDING_ACTION_STATUSES))
                .order_by(OperatorAction.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                operator_action_to_dict(action, senior)
                for action, senior in rows
            ]

    def update_action(
        self,
        action_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            action = db.get(OperatorAction, action_id)

            if not action:
                return None

            allowed_fields = {
                "status",
                "reason",
                "note",
                "target_contact_id",
                "created_by",
            }

            for field in allowed_fields:
                if field in payload:
                    setattr(action, field, payload[field])

            db.commit()
            db.refresh(action)

            senior = db.get(SeniorProfile, action.senior_id)

            return operator_action_to_dict(action, senior)


operator_action_service = OperatorActionService()