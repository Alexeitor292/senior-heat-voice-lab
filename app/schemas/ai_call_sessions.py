from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AICallTranscriptTurn(BaseModel):
    speaker: str = Field(default="senior")
    text: str = Field(..., min_length=1)
    started_at_ms: int | None = None
    ended_at_ms: int | None = None


class AICallSessionStartRequest(BaseModel):
    provider: str = Field(default="manual_adapter")
    provider_session_id: str | None = None
    senior_call_sid: str | None = None
    call_status: str = Field(default="in_progress")
    raw_provider_payload: dict[str, Any] = Field(default_factory=dict)


class AICallSessionTurnRequest(BaseModel):
    speaker: str = Field(default="senior")
    text: str = Field(..., min_length=1)
    started_at_ms: int | None = None
    ended_at_ms: int | None = None
    senior_call_sid: str | None = None
    provider_event_id: str | None = None
    raw_provider_payload: dict[str, Any] = Field(default_factory=dict)


class AICallSessionCompleteRequest(BaseModel):
    provider: str = Field(default="manual_adapter")
    provider_session_id: str | None = None

    senior_call_sid: str | None = None
    call_status: str = Field(default="completed")
    duration_seconds: int | None = None

    heat_risk_value: int | None = None
    heat_risk_label: str | None = None

    # Optional. If omitted, the backend uses transcript turns already appended
    # to this call session.
    transcript_turns: list[AICallTranscriptTurn] | None = None

    create_operator_actions: bool = True
    raw_provider_payload: dict[str, Any] = Field(default_factory=dict)


class AICallCompletionRequest(BaseModel):
    provider: str = Field(default="manual_adapter")
    provider_session_id: str | None = None

    senior_call_sid: str | None = None
    call_session_id: int | None = None

    call_status: str = Field(default="completed")
    duration_seconds: int | None = None

    heat_risk_value: int | None = None
    heat_risk_label: str | None = None

    transcript_turns: list[AICallTranscriptTurn]
    create_operator_actions: bool = True

    raw_provider_payload: dict[str, Any] = Field(default_factory=dict)


class AICallCompletionResponse(BaseModel):
    message: str
    provider: str
    senior_id: int
    senior_call_sid: str | None = None
    call_session_id: int | None = None
    check_in_id: int
    insight_id: int
    check_in_review_url: str
    analysis: dict[str, Any]
    operator_actions_created: list[dict]
    operator_actions_updated: list[dict] = Field(default_factory=list)
    operator_action_evidence: list[dict] = Field(default_factory=list)