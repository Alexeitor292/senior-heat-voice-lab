from __future__ import annotations

from pydantic import BaseModel, Field


class TranscriptTurnInput(BaseModel):
    speaker: str = Field(default="senior")
    text: str = Field(..., min_length=1)
    started_at_ms: int | None = None
    ended_at_ms: int | None = None


class RecommendedOperatorAction(BaseModel):
    action_type: str
    reason: str
    target_contact_id: int | None = None


class SafetyAssessment(BaseModel):
    risk_level: str
    confidence: float = 0.5
    summary: str
    escalation_needed: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    recommended_actions: list[RecommendedOperatorAction] = Field(default_factory=list)


class MemoryCandidate(BaseModel):
    type: str = "general"
    content: str
    confidence: float = 0.5


class RelationshipAssessment(BaseModel):
    conversation_summary: str
    mood_label: str = "unknown"
    loneliness_signal: str = "unknown"
    topics_discussed: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    memory_candidates: list[MemoryCandidate] = Field(default_factory=list)


class ConversationAnalysisResult(BaseModel):
    safety_assessment: SafetyAssessment
    relationship_assessment: RelationshipAssessment


class ConversationAnalysisRequest(BaseModel):
    senior_call_sid: str | None = None
    call_session_id: int | None = None
    heat_risk_value: int | None = None
    heat_risk_label: str | None = None
    transcript_turns: list[TranscriptTurnInput]
    create_operator_actions: bool = True


class ConversationAnalysisStoredResponse(BaseModel):
    message: str
    senior_id: int
    check_in_id: int
    insight_id: int
    analysis: ConversationAnalysisResult
    operator_actions_created: list[dict]