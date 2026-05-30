from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from app.db.database import SessionLocal
from app.db.models import (
    CheckIn,
    CheckInCallSession,
    ConversationInsight,
    HeatRiskObservation,
    OperatorAction,
    OperatorActionEvidence,
    SeniorMemoryCandidate,
    SeniorProfile,
    SupportContact,
    TranscriptTurn,
)
from app.schemas.conversation_analysis import (
    ConversationAnalysisRequest,
    ConversationAnalysisResult,
    MemoryCandidate,
    RecommendedOperatorAction,
    RelationshipAssessment,
    SafetyAssessment,
    TranscriptTurnInput,
)


ANALYZER_NAME = "rules_v0_conversation_companion"

HEAT_DISCOMFORT_PATTERNS = [
    "hot",
    "too warm",
    "no ac",
    "no air conditioning",
    "air conditioner broke",
    "can't cool",
    "cannot cool",
    "sweating",
]

HEAT_SYMPTOM_PATTERNS = [
    "dizzy",
    "lightheaded",
    "faint",
    "nauseous",
    "nausea",
    "weak",
    "confused",
    "headache",
    "chills",
    "cramps",
    "thirsty",
    "dehydrated",
    "haven't had water",
    "no water",
    "not drinking",
]

URGENT_PATTERNS = [
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "passed out",
    "fainted",
    "fall",
    "fell",
    "very confused",
    "emergency",
    "call 911",
]

LOW_MOOD_PATTERNS = [
    "sad",
    "lonely",
    "alone",
    "depressed",
    "tired of",
    "nobody",
    "no one visits",
    "miss",
    "worried",
    "anxious",
    "scared",
]

FOOD_SLEEP_ROUTINE_PATTERNS = [
    "didn't sleep",
    "did not sleep",
    "can't sleep",
    "cannot sleep",
    "haven't eaten",
    "didn't eat",
    "not hungry",
    "no appetite",
    "tired",
]


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


SENIOR_SPEAKER_LABELS = {"senior", "user", "caller"}


def _is_senior_turn(turn: TranscriptTurnInput) -> bool:
    return (turn.speaker or "").lower().strip() in SENIOR_SPEAKER_LABELS


def _senior_lower_text(turns: list[TranscriptTurnInput]) -> str:
    return " ".join(
        turn.text for turn in turns if _is_senior_turn(turn)
    ).lower()

def _full_transcript(turns: list[TranscriptTurnInput]) -> str:
    lines = []

    for turn in turns:
        speaker = (turn.speaker or "unknown").strip()
        lines.append(f"{speaker}: {turn.text.strip()}")

    return "\n".join(lines)


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def _matched_patterns(text: str, patterns: list[str]) -> list[str]:
    return [pattern for pattern in patterns if pattern in text]


def _senior_turn_text(turns: list[TranscriptTurnInput]) -> str:
    return " ".join(
        turn.text
        for turn in turns
        if _is_senior_turn(turn)
    )


def _normalize_for_matching(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )

    return without_accents.casefold()


def _phrase_exists(text: str, phrase: str) -> bool:
    normalized_text = _normalize_for_matching(text)
    normalized_phrase = _normalize_for_matching(phrase).strip()

    if not normalized_phrase:
        return False

    # This is not entity extraction. It is exact known-name matching with boundaries.
    # It prevents false positives like matching "Ana" inside "banana".
    pattern = rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)"

    return re.search(pattern, normalized_text) is not None


def _contact_aliases(contact: SupportContact) -> list[str]:
    full_name = (contact.name or "").strip()

    if not full_name:
        return []

    aliases = [full_name]

    first_name = full_name.split()[0].strip()

    if len(first_name) >= 3 and first_name not in aliases:
        aliases.append(first_name)

    return aliases


def _known_support_contact_mentions(
    senior_id: int,
    turns: list[TranscriptTurnInput],
) -> list[dict[str, Any]]:
    senior_text = _senior_turn_text(turns)

    if not senior_text.strip():
        return []

    with SessionLocal() as db:
        contacts = (
            db.query(SupportContact)
            .filter(SupportContact.senior_id == senior_id)
            .filter(SupportContact.is_active.is_(True))
            .order_by(SupportContact.priority.asc(), SupportContact.id.asc())
            .all()
        )

    mentions: list[dict[str, Any]] = []

    for contact in contacts:
        matched_alias = None

        for alias in _contact_aliases(contact):
            if _phrase_exists(senior_text, alias):
                matched_alias = alias
                break

        if not matched_alias:
            continue

        mentions.append(
            {
                "id": contact.id,
                "name": contact.name,
                "matched_alias": matched_alias,
                "relationship": contact.relationship,
                "contact_type": contact.contact_type,
                "priority": contact.priority,
                "can_receive_alerts": contact.can_receive_alerts,
                "is_emergency_contact": contact.is_emergency_contact,
            }
        )

    return mentions


def _latest_heat_context(
    senior_id: int,
    explicit_value: int | None,
    explicit_label: str | None,
) -> tuple[int | None, str | None]:
    if explicit_value is not None or explicit_label is not None:
        return explicit_value, explicit_label

    with SessionLocal() as db:
        row = (
            db.query(HeatRiskObservation)
            .filter(HeatRiskObservation.senior_id == senior_id)
            .order_by(HeatRiskObservation.observed_at.desc())
            .first()
        )

        if not row:
            return None, None

        return row.heat_risk_value, row.heat_risk_label


def _action_type_label(action_type: str) -> str:
    labels = {
        "operator_review": "operator review",
        "message_support": "support outreach",
        "wellness_check": "wellness check",
        "call_senior": "senior callback",
    }

    return labels.get(action_type, action_type.replace("_", " "))


def _recommended_action_summary(
    actions: list[RecommendedOperatorAction],
    risk_level: str,
) -> str | None:
    if not actions:
        return None

    action_types = [action.action_type for action in actions]
    labels = [_action_type_label(action_type) for action_type in action_types]

    if len(labels) == 1:
        return f"{labels[0].capitalize()} recommended"

    if len(labels) == 2:
        return f"{labels[0].capitalize()} + {labels[1]} recommended"

    return f"{risk_level.capitalize()} follow-up recommended: " + ", ".join(labels)


def _operator_action_evidence_to_dict(row: OperatorActionEvidence) -> dict[str, Any]:
    return {
        "id": row.id,
        "operator_action_id": row.operator_action_id,
        "senior_id": row.senior_id,
        "check_in_id": row.check_in_id,
        "conversation_insight_id": row.conversation_insight_id,
        "source": row.source,
        "reason": row.reason,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _ensure_operator_action_evidence(
    db,
    operator_action: OperatorAction,
    senior_id: int,
    check_in_id: int,
    insight_id: int | None,
    reason: str,
) -> OperatorActionEvidence:
    existing = (
        db.query(OperatorActionEvidence)
        .filter(OperatorActionEvidence.operator_action_id == operator_action.id)
        .filter(OperatorActionEvidence.check_in_id == check_in_id)
        .first()
    )

    if existing:
        return existing

    evidence = OperatorActionEvidence(
        operator_action_id=operator_action.id,
        senior_id=senior_id,
        check_in_id=check_in_id,
        conversation_insight_id=insight_id,
        source="ai_conversation_analysis",
        reason=reason,
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


def _operator_action_to_summary_dict(row: OperatorAction) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "action_type": row.action_type,
        "status": row.status,
        "reason": row.reason,
        "note": row.note,
        "target_contact_id": row.target_contact_id,
        "created_by": row.created_by,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }

def analyze_conversation(
    senior_id: int,
    turns: list[TranscriptTurnInput],
    heat_risk_value: int | None = None,
    heat_risk_label: str | None = None,
) -> ConversationAnalysisResult:
    text = _senior_lower_text(turns)
    original_text = _senior_turn_text(turns)

    reason_codes: list[str] = []
    recommended_actions: list[RecommendedOperatorAction] = []

    heat_symptoms = _matched_patterns(text, HEAT_SYMPTOM_PATTERNS)
    urgent_signals = _matched_patterns(text, URGENT_PATTERNS)
    heat_discomfort = _matched_patterns(text, HEAT_DISCOMFORT_PATTERNS)
    low_mood = _matched_patterns(text, LOW_MOOD_PATTERNS)
    routine_signals = _matched_patterns(text, FOOD_SLEEP_ROUTINE_PATTERNS)

    known_contact_mentions = _known_support_contact_mentions(
        senior_id=senior_id,
        turns=turns,
    )

    primary_mentioned_contact_id = (
        known_contact_mentions[0]["id"] if known_contact_mentions else None
    )

    if heat_risk_value is not None and heat_risk_value >= 3:
        reason_codes.append("heat_risk_major_or_higher")
    elif heat_risk_value is not None and heat_risk_value >= 2:
        reason_codes.append("heat_risk_moderate")

    if heat_discomfort:
        reason_codes.append("reported_heat_discomfort")

    if heat_symptoms:
        reason_codes.append("reported_heat_symptoms")

    if urgent_signals:
        reason_codes.append("urgent_safety_language")

    if low_mood:
        reason_codes.append("low_mood_or_loneliness_signal")

    if routine_signals:
        reason_codes.append("routine_or_self_care_concern")

    risk_level = "green"
    confidence = 0.62

    if urgent_signals:
        risk_level = "red"
        confidence = 0.9
    elif heat_symptoms and heat_risk_value is not None and heat_risk_value >= 3:
        risk_level = "orange"
        confidence = 0.84
    elif heat_symptoms or (heat_discomfort and heat_risk_value is not None and heat_risk_value >= 2):
        risk_level = "yellow"
        confidence = 0.76
    elif low_mood or routine_signals:
        risk_level = "yellow"
        confidence = 0.68

    escalation_needed = risk_level in {"yellow", "orange", "red"}

    if risk_level == "red":
        recommended_actions.append(
            RecommendedOperatorAction(
                action_type="operator_review",
                reason="Conversation included urgent safety language that requires immediate operator review.",
            )
        )
        recommended_actions.append(
            RecommendedOperatorAction(
                action_type="wellness_check",
                reason="Senior may need an urgent in-person wellness check based on call content.",
            )
        )
    elif risk_level == "orange":
        recommended_actions.append(
            RecommendedOperatorAction(
                action_type="operator_review",
                reason="Senior reported concerning symptoms during major heat conditions.",
            )
        )
        recommended_actions.append(
            RecommendedOperatorAction(
                action_type="message_support",
                reason="Support contact should check on the senior after concerning heat-related symptoms.",
                target_contact_id=primary_mentioned_contact_id,
            )
        )
    elif risk_level == "yellow":
        recommended_actions.append(
            RecommendedOperatorAction(
                action_type="message_support",
                reason="Senior may benefit from a support check-in based on the conversation.",
                target_contact_id=primary_mentioned_contact_id,
            )
        )

    if not reason_codes:
        reason_codes.append("no_major_concern_detected")

    safety_summary = "No major safety concerns detected."
    if risk_level == "yellow":
        safety_summary = "Mild concern detected from the conversation. Follow-up support may be helpful."
    elif risk_level == "orange":
        safety_summary = "Moderate concern detected. Operator review and support outreach are recommended."
    elif risk_level == "red":
        safety_summary = "Urgent concern detected. Immediate operator review is recommended."

    topics = []

    if heat_discomfort or heat_symptoms or heat_risk_value is not None:
        topics.append("heat safety")

    if low_mood:
        topics.append("mood or loneliness")

    if routine_signals:
        topics.append("sleep, food, or routine")

    for mention in known_contact_mentions:
        topics.append(mention["name"])

    topics = list(dict.fromkeys(topics))[:8]

    mood_label = "neutral"
    loneliness_signal = "low"

    if low_mood:
        mood_label = "low"
        loneliness_signal = "elevated"
    elif routine_signals:
        mood_label = "tired"

    follow_up_suggestions = []

    if "heat safety" in topics:
        follow_up_suggestions.append("Ask whether the home feels cooler and whether they have had water.")

    if loneliness_signal == "elevated":
        follow_up_suggestions.append("Ask whether a family member or support contact checked in recently.")

    if "sleep, food, or routine" in topics:
        follow_up_suggestions.append("Ask whether sleep, appetite, or energy improved since the last call.")

    if not follow_up_suggestions:
        follow_up_suggestions.append("Continue with a warm general check-in and ask how the day is going.")

    memory_candidates: list[MemoryCandidate] = []

    for mention in known_contact_mentions:
        relationship = mention.get("relationship")
        relationship_text = f" ({relationship})" if relationship else ""

        memory_candidates.append(
            MemoryCandidate(
                type="known_support_contact_mention",
                content=(
                    f"The senior mentioned {mention['name']}{relationship_text} "
                    "during the conversation."
                ),
                confidence=0.9,
            )
        )

    if loneliness_signal == "elevated":
        memory_candidates.append(
            MemoryCandidate(
                type="emotional_context",
                content="The senior may appreciate gentle follow-up about social connection.",
                confidence=0.65,
            )
        )

    relationship_summary = "Senior completed a brief welfare conversation."

    if topics:
        relationship_summary = (
            "Senior discussed " + ", ".join(topics[:4]) + "."
        )

    return ConversationAnalysisResult(
        safety_assessment=SafetyAssessment(
            risk_level=risk_level,
            confidence=confidence,
            summary=safety_summary,
            escalation_needed=escalation_needed,
            reason_codes=reason_codes,
            recommended_actions=recommended_actions,
        ),
        relationship_assessment=RelationshipAssessment(
            conversation_summary=relationship_summary,
            mood_label=mood_label,
            loneliness_signal=loneliness_signal,
            topics_discussed=topics,
            follow_up_suggestions=follow_up_suggestions,
            memory_candidates=memory_candidates,
        ),
    )


class AIConversationAnalysisService:
    def analyze_and_store(
        self,
        senior_id: int,
        request: ConversationAnalysisRequest,
    ) -> dict[str, Any] | None:
        heat_risk_value, heat_risk_label = _latest_heat_context(
            senior_id=senior_id,
            explicit_value=request.heat_risk_value,
            explicit_label=request.heat_risk_label,
        )

        analysis = analyze_conversation(
            senior_id=senior_id,
            turns=request.transcript_turns,
            heat_risk_value=heat_risk_value,
            heat_risk_label=heat_risk_label,
        )

        transcript = _full_transcript(request.transcript_turns)

        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            call_session = None

            if request.call_session_id:
                call_session = db.get(CheckInCallSession, request.call_session_id)

            check_in = CheckIn(
                source="ai_conversation_analysis",
                senior_phone_number=senior.phone_number,
                senior_call_sid=request.senior_call_sid,
                senior_call_status="completed",
                transcript=transcript,
                risk_level=analysis.safety_assessment.risk_level,
                reported_symptoms_json=_json(
                    analysis.safety_assessment.reason_codes
                ),
                red_flags_json=_json(
                    [
                        code
                        for code in analysis.safety_assessment.reason_codes
                        if code
                        in {
                            "reported_heat_symptoms",
                            "urgent_safety_language",
                            "heat_risk_major_or_higher",
                        }
                    ]
                ),
                orientation_concern="urgent_safety_language"
                in analysis.safety_assessment.reason_codes,
                escalation_needed=analysis.safety_assessment.escalation_needed,
                caregiver_summary=analysis.relationship_assessment.conversation_summary,
                recommended_action=_recommended_action_summary(
                    analysis.safety_assessment.recommended_actions,
                    analysis.safety_assessment.risk_level,
                ),
                confidence_notes=f"Confidence: {analysis.safety_assessment.confidence:.2f}",
                analyzer=ANALYZER_NAME,
                raw_analysis_json=analysis.model_dump_json(),
                caregiver_alert_required=False,
                caregiver_alert_sent=False,
            )

            db.add(check_in)
            db.commit()
            db.refresh(check_in)

            existing_session_turns = []

            if request.call_session_id:
                existing_session_turns = (
                    db.query(TranscriptTurn)
                    .filter(TranscriptTurn.call_session_id == request.call_session_id)
                    .order_by(TranscriptTurn.turn_index.asc())
                    .all()
                )

            if existing_session_turns:
                for row in existing_session_turns:
                    row.check_in_id = check_in.id

                    if request.senior_call_sid:
                        row.senior_call_sid = request.senior_call_sid
            else:
                for index, turn in enumerate(request.transcript_turns):
                    db.add(
                        TranscriptTurn(
                            senior_id=senior_id,
                            check_in_id=check_in.id,
                            call_session_id=request.call_session_id,
                            senior_call_sid=request.senior_call_sid,
                            turn_index=index,
                            speaker=turn.speaker,
                            text=turn.text,
                            started_at_ms=turn.started_at_ms,
                            ended_at_ms=turn.ended_at_ms,
                        )
                    )

            insight = ConversationInsight(
                senior_id=senior_id,
                check_in_id=check_in.id,
                call_session_id=request.call_session_id,
                senior_call_sid=request.senior_call_sid,
                safety_risk_level=analysis.safety_assessment.risk_level,
                safety_confidence=analysis.safety_assessment.confidence,
                safety_summary=analysis.safety_assessment.summary,
                safety_escalation_needed=analysis.safety_assessment.escalation_needed,
                safety_reason_codes_json=_json(
                    analysis.safety_assessment.reason_codes
                ),
                relationship_summary=analysis.relationship_assessment.conversation_summary,
                mood_label=analysis.relationship_assessment.mood_label,
                loneliness_signal=analysis.relationship_assessment.loneliness_signal,
                topics_discussed_json=_json(
                    analysis.relationship_assessment.topics_discussed
                ),
                follow_up_suggestions_json=_json(
                    analysis.relationship_assessment.follow_up_suggestions
                ),
                recommended_actions_json=_json(
                    [
                        action.model_dump()
                        for action in analysis.safety_assessment.recommended_actions
                    ]
                ),
                memory_candidates_json=_json(
                    [
                        memory.model_dump()
                        for memory in analysis.relationship_assessment.memory_candidates
                    ]
                ),
                analyzer=ANALYZER_NAME,
                raw_analysis_json=analysis.model_dump_json(),
            )

            db.add(insight)
            db.commit()
            db.refresh(insight)

            for memory in analysis.relationship_assessment.memory_candidates:
                db.add(
                    SeniorMemoryCandidate(
                        senior_id=senior_id,
                        check_in_id=check_in.id,
                        insight_id=insight.id,
                        memory_type=memory.type,
                        content=memory.content,
                        confidence=memory.confidence,
                    )
                )

            operator_actions_created = []
            operator_actions_updated = []
            operator_action_evidence = []

            if request.create_operator_actions:
                for action in analysis.safety_assessment.recommended_actions:
                    existing_pending = (
                        db.query(OperatorAction)
                        .filter(OperatorAction.senior_id == senior_id)
                        .filter(OperatorAction.action_type == action.action_type)
                        .filter(OperatorAction.status.in_(["requested", "in_progress"]))
                        .first()
                    )

                    if existing_pending:
                        evidence = _ensure_operator_action_evidence(
                            db=db,
                            operator_action=existing_pending,
                            senior_id=senior_id,
                            check_in_id=check_in.id,
                            insight_id=insight.id,
                            reason=action.reason,
                        )

                        db.refresh(existing_pending)

                        operator_actions_updated.append(
                            _operator_action_to_summary_dict(existing_pending)
                        )
                        operator_action_evidence.append(
                            _operator_action_evidence_to_dict(evidence)
                        )

                        continue

                    operator_action = OperatorAction(
                        senior_id=senior_id,
                        action_type=action.action_type,
                        status="requested",
                        reason=action.reason,
                        note=None,
                        target_contact_id=action.target_contact_id,
                        created_by="ai_conversation_analysis",
                    )

                    db.add(operator_action)
                    db.commit()
                    db.refresh(operator_action)

                    operator_actions_created.append(
                        _operator_action_to_summary_dict(operator_action)
                    )

                    evidence = _ensure_operator_action_evidence(
                        db=db,
                        operator_action=operator_action,
                        senior_id=senior_id,
                        check_in_id=check_in.id,
                        insight_id=insight.id,
                        reason=action.reason,
                    )

                    operator_action_evidence.append(
                        _operator_action_evidence_to_dict(evidence)
                    )

            db.commit()

            return {
                "senior_id": senior_id,
                "check_in_id": check_in.id,
                "insight_id": insight.id,
                "analysis": analysis.model_dump(),
                "operator_actions_created": operator_actions_created,
                "operator_actions_updated": operator_actions_updated,
                "operator_action_evidence": operator_action_evidence,
            }

    def list_insights_for_senior(
        self,
        senior_id: int,
        limit: int = 25,
    ) -> list[dict[str, Any]] | None:
        with SessionLocal() as db:
            senior = db.get(SeniorProfile, senior_id)

            if not senior:
                return None

            rows = (
                db.query(ConversationInsight)
                .filter(ConversationInsight.senior_id == senior_id)
                .order_by(ConversationInsight.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": row.id,
                    "senior_id": row.senior_id,
                    "check_in_id": row.check_in_id,
                    "call_session_id": row.call_session_id,
                    "senior_call_sid": row.senior_call_sid,
                    "safety_risk_level": row.safety_risk_level,
                    "safety_confidence": row.safety_confidence,
                    "safety_summary": row.safety_summary,
                    "safety_escalation_needed": row.safety_escalation_needed,
                    "safety_reason_codes": json.loads(row.safety_reason_codes_json or "[]"),
                    "relationship_summary": row.relationship_summary,
                    "mood_label": row.mood_label,
                    "loneliness_signal": row.loneliness_signal,
                    "topics_discussed": json.loads(row.topics_discussed_json or "[]"),
                    "follow_up_suggestions": json.loads(row.follow_up_suggestions_json or "[]"),
                    "recommended_actions": json.loads(row.recommended_actions_json or "[]"),
                    "memory_candidates": json.loads(row.memory_candidates_json or "[]"),
                    "analyzer": row.analyzer,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]


ai_conversation_analysis_service = AIConversationAnalysisService()