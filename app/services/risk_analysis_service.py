import json
from typing import Any

from openai import OpenAI

from app.config import settings


HEAT_CHECK_RISK_SCHEMA = {
    "type": "object",
    "properties": {
        "risk_level": {
            "type": "string",
            "enum": ["GREEN", "YELLOW", "RED", "UNKNOWN"],
            "description": "Overall risk level based only on the provided transcript."
        },
        "reported_symptoms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Symptoms or concerns explicitly mentioned by the caller."
        },
        "red_flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Urgent warning signs such as confusion, fainting, collapse, seizure, or inability to stand."
        },
        "orientation_concern": {
            "type": "boolean",
            "description": "True if the caller sounds confused, disoriented, incoherent, or unable to answer basic questions."
        },
        "escalation_needed": {
            "type": "boolean",
            "description": "True if a caregiver should be alerted based on this transcript."
        },
        "caregiver_summary": {
            "type": "string",
            "description": "Short plain-English summary for a caregiver."
        },
        "recommended_action": {
            "type": "string",
            "description": "Short recommended next action for the caregiver."
        },
        "confidence_notes": {
            "type": "string",
            "description": "Any uncertainty, transcript limitations, or why the risk level was chosen."
        }
    },
    "required": [
        "risk_level",
        "reported_symptoms",
        "red_flags",
        "orientation_concern",
        "escalation_needed",
        "caregiver_summary",
        "recommended_action",
        "confidence_notes"
    ],
    "additionalProperties": False
}


class RiskAnalysisService:
    def __init__(self):
        self.client = None

        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)

    def analyze_transcript(
        self,
        transcript: str,
        speech_confidence: str | None = None
    ) -> dict[str, Any]:
        """
        Analyze a speech transcript from a heat-safety check-in call.

        This is not a medical diagnosis.
        This is an early warning and caregiver escalation helper.
        """

        transcript = (transcript or "").strip()

        if not transcript:
            return {
                "risk_level": "UNKNOWN",
                "reported_symptoms": [],
                "red_flags": [],
                "orientation_concern": False,
                "escalation_needed": True,
                "caregiver_summary": "No clear spoken response was captured during the heat-safety check-in.",
                "recommended_action": "Caregiver should follow up because the system could not confirm the person is okay.",
                "confidence_notes": "No transcript was received from the speech capture step.",
                "analyzer": "local_fallback"
            }

        if not self.client:
            fallback = self._keyword_fallback(transcript)
            fallback["analyzer"] = "local_keyword_fallback_no_openai_key"
            return fallback

        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You analyze transcripts from a senior heat-safety check-in call. "
                            "You are not diagnosing heat stroke or any medical condition. "
                            "Your job is to identify concerning statements that may require caregiver follow-up. "
                            "Use GREEN only when the person clearly sounds okay and reports no concerning symptoms. "
                            "Use YELLOW when they mention dizziness, weakness, nausea, headache, dehydration, feeling very hot, "
                            "not feeling well, being outside in heat, or uncertainty. "
                            "Use RED when they mention confusion, fainting, collapse, seizure, inability to stand, severe distress, "
                            "or if their response suggests disorientation or incoherence. "
                            "Use UNKNOWN if the transcript is too unclear to assess. "
                            "When uncertain, lean toward caregiver follow-up instead of ignoring risk."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            "Analyze this heat-safety check-in transcript.\n\n"
                            f"Transcript: {transcript}\n"
                            f"Speech confidence from phone transcription: {speech_confidence or 'not provided'}"
                        )
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "heat_check_risk_analysis",
                        "strict": True,
                        "schema": HEAT_CHECK_RISK_SCHEMA
                    }
                }
            )

            raw_content = response.choices[0].message.content
            analysis = json.loads(raw_content)

            analysis["analyzer"] = "openai_structured_output"
            analysis["source_transcript"] = transcript
            analysis["speech_confidence"] = speech_confidence

            return analysis

        except Exception as exc:
            fallback = self._keyword_fallback(transcript)
            fallback["analyzer"] = "local_keyword_fallback_after_openai_error"
            fallback["llm_error"] = str(exc)
            return fallback

    def _keyword_fallback(self, transcript: str) -> dict[str, Any]:
        """
        Backup classifier in case OpenAI is unavailable.

        This keeps the demo working even if API key, quota, network,
        or schema issues happen.
        """

        text = transcript.lower()

        red_keywords = [
            "confused",
            "can't think",
            "cannot think",
            "passed out",
            "fainted",
            "seizure",
            "collapsed",
            "can't stand",
            "cannot stand",
            "incoherent",
            "don't know where i am",
            "do not know where i am"
        ]

        yellow_keywords = [
            "dizzy",
            "weak",
            "nauseous",
            "nausea",
            "headache",
            "tired",
            "hot",
            "dehydrated",
            "thirsty",
            "not okay",
            "not feeling good",
            "sick",
            "lightheaded",
            "cramps"
        ]

        red_flags = [
            keyword for keyword in red_keywords
            if keyword in text
        ]

        symptoms = [
            keyword for keyword in yellow_keywords
            if keyword in text
        ]

        if red_flags:
            return {
                "risk_level": "RED",
                "reported_symptoms": symptoms,
                "red_flags": red_flags,
                "orientation_concern": True,
                "escalation_needed": True,
                "caregiver_summary": (
                    "The caller mentioned a possible urgent warning sign during the heat-safety check-in."
                ),
                "recommended_action": (
                    "Caregiver should contact the person immediately and consider emergency help if symptoms are serious."
                ),
                "confidence_notes": (
                    f"Local fallback detected urgent keywords: {', '.join(red_flags)}."
                )
            }

        if symptoms:
            return {
                "risk_level": "YELLOW",
                "reported_symptoms": symptoms,
                "red_flags": [],
                "orientation_concern": False,
                "escalation_needed": True,
                "caregiver_summary": (
                    "The caller mentioned symptoms or discomfort during the heat-safety check-in."
                ),
                "recommended_action": (
                    "Caregiver should call or check on the person soon."
                ),
                "confidence_notes": (
                    f"Local fallback detected concern keywords: {', '.join(symptoms)}."
                )
            }

        return {
            "risk_level": "GREEN",
            "reported_symptoms": [],
            "red_flags": [],
            "orientation_concern": False,
            "escalation_needed": False,
            "caregiver_summary": (
                "The caller did not mention obvious concerning symptoms in this check-in."
            ),
            "recommended_action": (
                "No immediate caregiver action from this test transcript."
            ),
            "confidence_notes": (
                "Local fallback found no concern keywords."
            )
        }


risk_analysis_service = RiskAnalysisService()