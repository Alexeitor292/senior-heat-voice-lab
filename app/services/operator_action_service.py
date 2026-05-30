from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.db.database import SessionLocal
from app.db.models import OperatorAction, OperatorActionEvidence, SeniorProfile


PENDING_ACTION_STATUSES = {"requested", "in_progress"}


def _iso(value):
    return value.isoformat() if value else None


def operator_action_evidence_to_dict(
    row: OperatorActionEvidence,
) -> dict[str, Any]:
    return {
        "id": row.id,
        "operator_action_id": row.operator_action_id,
        "senior_id": row.senior_id,
        "check_in_id": row.check_in_id,
        "conversation_insight_id": row.conversation_insight_id,
        "source": row.source,
        "reason": row.reason,
        "created_at": _iso(row.created_at),
    }


def operator_action_to_dict(
    row: OperatorAction,
    senior: SeniorProfile | None = None,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    action_evidence = evidence or []

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
        "evidence": action_evidence,
        "evidence_count": len(action_evidence),
    }

    if senior is not None:
        result["senior_name"] = senior.name
        result["senior_phone_number"] = senior.phone_number

    return result


def _load_evidence_by_action_id(
    db,
    action_ids: list[int],
) -> dict[int, list[dict[str, Any]]]:
    if not action_ids:
        return {}

    rows = (
        db.query(OperatorActionEvidence)
        .filter(OperatorActionEvidence.operator_action_id.in_(action_ids))
        .order_by(OperatorActionEvidence.created_at.desc())
        .all()
    )

    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        grouped[row.operator_action_id].append(
            operator_action_evidence_to_dict(row)
        )

    return dict(grouped)


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

            evidence_by_action_id = _load_evidence_by_action_id(
                db=db,
                action_ids=[row.id for row in rows],
            )

            return [
                operator_action_to_dict(
                    row,
                    senior,
                    evidence=evidence_by_action_id.get(row.id, []),
                )
                for row in rows
            ]

    def list_actions(
        self,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        normalized_status = (status or "all").lower().strip()

        with SessionLocal() as db:
            query = (
                db.query(OperatorAction, SeniorProfile)
                .join(SeniorProfile, OperatorAction.senior_id == SeniorProfile.id)
            )

            if normalized_status == "pending":
                query = query.filter(OperatorAction.status.in_(PENDING_ACTION_STATUSES))
            elif normalized_status != "all":
                query = query.filter(OperatorAction.status == normalized_status)

            rows = (
                query
                .order_by(OperatorAction.created_at.desc())
                .limit(limit)
                .all()
            )

            action_ids = [action.id for action, _senior in rows]
            evidence_by_action_id = _load_evidence_by_action_id(
                db=db,
                action_ids=action_ids,
            )

            return [
                operator_action_to_dict(
                    action,
                    senior,
                    evidence=evidence_by_action_id.get(action.id, []),
                )
                for action, senior in rows
            ]

    def list_pending_actions(
        self,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self.list_actions(status="pending", limit=limit)

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
            evidence_by_action_id = _load_evidence_by_action_id(
                db=db,
                action_ids=[action.id],
            )

            return operator_action_to_dict(
                action,
                senior,
                evidence=evidence_by_action_id.get(action.id, []),
            )


operator_action_service = OperatorActionService()