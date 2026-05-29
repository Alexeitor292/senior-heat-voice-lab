"""
Tests for safe_logging redaction.

All tests run with LOG_PII=false, LOG_TRANSCRIPTS=false, LOG_RAW_ANALYSIS=false
(set in conftest.py) — the default production-safe mode.
"""
import json

import pytest

from app.utils.safe_logging import (
    mask_call_sid,
    mask_phone_number,
    safe_alert_result_for_logging,
    safe_baseline_comparison_for_logging,
    safe_json_dumps,
    safe_log_object,
)


# ---------------------------------------------------------------------------
# Shared test payload (mirrors the spec example)
# ---------------------------------------------------------------------------

FULL_PAYLOAD = {
    "senior_name": "Juan Test Senior",
    "profile_senior_name": "Juan Test Senior",
    "caregiver_summary": "Senior reported dizziness and confusion",
    "recommended_action": "Call Juan immediately",
    "reported_symptoms": ["dizziness"],
    "red_flags": ["confusion"],
    "message_preview": {
        "senior_name": "Juan Test Senior",
        "transcript": "I feel dizzy",
        "caregiver_summary": "Senior may need help",
        "recommended_action": "Check in immediately",
        "source_call_sid": "CAe4d701a766952b942128032185b2c6d1",
    },
    "baseline_comparison": {
        "baseline_transcript": "I am feeling okay today",
        "current_transcript": "I feel dizzy",
        "baseline_deviation_level": "RED",
        "baseline_word_count": 12,
        "current_word_count": 3,
    },
    "transcript": "I feel dizzy",
    "to": "+19169472666",
    "from_number": "+19165551234",
    "call_sid": "CAe4d701a766952b942128032185b2c6d1",
    "risk_level": "RED",
    "alert_sent": True,
    "alert_id": 123,
}

FULL_SID = "CAe4d701a766952b942128032185b2c6d1"
PHONE_CAREGIVER = "+19169472666"
PHONE_SENIOR = "+19165551234"
SENIOR_NAME = "Juan Test Senior"
TRANSCRIPT = "I feel dizzy"
BASELINE_TRANSCRIPT = "I am feeling okay today"
CAREGIVER_SUMMARY = "Senior reported dizziness and confusion"
RECOMMENDED_ACTION = "Call Juan immediately"
CAREGIVER_SUMMARY_NESTED = "Senior may need help"
RECOMMENDED_ACTION_NESTED = "Check in immediately"


def _dumps(value) -> str:
    return safe_json_dumps(value)


# ---------------------------------------------------------------------------
# mask_phone_number
# ---------------------------------------------------------------------------

class TestMaskPhoneNumber:
    def test_e164_masked(self):
        result = mask_phone_number("+19169472666")
        assert result == "+1******2666"
        assert PHONE_CAREGIVER not in result

    def test_short_number_hidden(self):
        result = mask_phone_number("+123")
        assert result == "[phone hidden]"

    def test_none_returns_none(self):
        assert mask_phone_number(None) is None


# ---------------------------------------------------------------------------
# mask_call_sid
# ---------------------------------------------------------------------------

class TestMaskCallSid:
    def test_sid_masked(self):
        result = mask_call_sid(FULL_SID)
        assert FULL_SID not in result
        assert result.startswith("CAe4")
        assert result.endswith("c6d1")

    def test_short_sid_hidden(self):
        result = mask_call_sid("CA123")
        assert result == "[id hidden]"

    def test_none_returns_none(self):
        assert mask_call_sid(None) is None


# ---------------------------------------------------------------------------
# safe_log_object / safe_json_dumps — field-level redaction
# ---------------------------------------------------------------------------

class TestSafeLogObject:
    def _redacted(self):
        return _dumps(FULL_PAYLOAD)

    # --- identity ---

    def test_senior_name_hidden(self):
        assert SENIOR_NAME not in self._redacted()

    def test_profile_senior_name_hidden(self):
        # "senior_name" is a substring of "profile_senior_name"
        redacted = safe_log_object({"profile_senior_name": SENIOR_NAME})
        assert SENIOR_NAME not in json.dumps(redacted)

    # --- phone numbers ---

    def test_caregiver_phone_redacted(self):
        assert PHONE_CAREGIVER not in self._redacted()

    def test_senior_phone_redacted(self):
        assert PHONE_SENIOR not in self._redacted()

    def test_to_field_phone_redacted(self):
        # "to" key doesn't match keyword lists but the E.164 value is caught
        # by redact_string in the fallthrough path
        result = _dumps({"to": PHONE_CAREGIVER})
        assert PHONE_CAREGIVER not in result

    # --- transcripts ---

    def test_transcript_hidden(self):
        assert TRANSCRIPT not in self._redacted()

    def test_baseline_transcript_hidden(self):
        assert BASELINE_TRANSCRIPT not in self._redacted()

    def test_current_transcript_hidden(self):
        result = _dumps({"current_transcript": TRANSCRIPT})
        assert TRANSCRIPT not in result

    # --- health content ---

    def test_caregiver_summary_hidden(self):
        assert CAREGIVER_SUMMARY not in self._redacted()

    def test_recommended_action_hidden(self):
        assert RECOMMENDED_ACTION not in self._redacted()

    def test_symptoms_hidden(self):
        assert "dizziness" not in self._redacted()

    def test_red_flags_hidden(self):
        assert "confusion" not in self._redacted()

    def test_symptoms_list_shows_count(self):
        redacted = safe_log_object({"reported_symptoms": ["a", "b", "c"]})
        assert redacted["reported_symptoms"] == {"hidden": True, "count": 3}

    def test_red_flags_list_shows_count(self):
        redacted = safe_log_object({"red_flags": ["x"]})
        assert redacted["red_flags"] == {"hidden": True, "count": 1}

    # --- message_preview ---

    def test_message_preview_not_exposed(self):
        # Nested content inside message_preview must not appear
        assert SENIOR_NAME not in self._redacted()
        assert TRANSCRIPT not in self._redacted()
        assert CAREGIVER_SUMMARY_NESTED not in self._redacted()
        assert RECOMMENDED_ACTION_NESTED not in self._redacted()

    def test_message_preview_replaced_with_presence_flag(self):
        redacted = safe_log_object({"message_preview": {"senior_name": SENIOR_NAME}})
        assert redacted["message_preview"] == {"present": True}

    def test_message_preview_none_shows_not_present(self):
        redacted = safe_log_object({"message_preview": None})
        assert redacted["message_preview"] == {"present": False}

    # --- call SIDs ---

    def test_call_sid_masked(self):
        assert FULL_SID not in self._redacted()

    def test_call_sid_prefix_visible(self):
        redacted = safe_log_object({"call_sid": FULL_SID})
        assert redacted["call_sid"].startswith("CAe4")

    # --- safe debugging fields preserved ---

    def test_risk_level_preserved(self):
        redacted = safe_log_object(FULL_PAYLOAD)
        assert redacted["risk_level"] == "RED"

    def test_alert_sent_preserved(self):
        redacted = safe_log_object(FULL_PAYLOAD)
        assert redacted["alert_sent"] is True

    def test_alert_id_preserved(self):
        redacted = safe_log_object(FULL_PAYLOAD)
        assert redacted["alert_id"] == 123

    def test_baseline_deviation_level_preserved(self):
        redacted = safe_log_object(FULL_PAYLOAD)
        assert redacted["baseline_comparison"]["baseline_deviation_level"] == "RED"

    def test_baseline_numeric_metrics_preserved(self):
        redacted = safe_log_object(FULL_PAYLOAD)
        bc = redacted["baseline_comparison"]
        assert bc["baseline_word_count"] == 12
        assert bc["current_word_count"] == 3

    # --- transcript metadata ---

    def test_transcript_shows_metadata_not_content(self):
        redacted = safe_log_object({"transcript": TRANSCRIPT})
        t = redacted["transcript"]
        assert isinstance(t, dict)
        assert t["hidden"] is True
        assert "length_chars" in t
        assert "approx_words" in t


# ---------------------------------------------------------------------------
# safe_alert_result_for_logging
# ---------------------------------------------------------------------------

ALERT_SUCCESS = {
    "alert_sent": True,
    "alert_type": "voice_call",
    "alert_kind": "speech_risk",
    "risk_level": "RED",
    "to": PHONE_CAREGIVER,
    "alert_id": 42,
    "caregiver_call_sid": FULL_SID,
    "message_preview": {
        "senior_name": SENIOR_NAME,
        "transcript": TRANSCRIPT,
        "caregiver_summary": CAREGIVER_SUMMARY,
    },
}

ALERT_FAILURE = {
    "alert_sent": False,
    "alert_type": "voice_call",
    "alert_kind": "speech_risk",
    "risk_level": "RED",
    "to": PHONE_CAREGIVER,
    "alert_id": 43,
    "error": "Connection refused",
    "message_preview": {"senior_name": SENIOR_NAME},
}

ALERT_SKIPPED = {
    "alert_sent": False,
    "alert_type": "voice_call",
    "reason": "Risk level does not require caregiver alert.",
    "risk_level": "GREEN",
}

ALERT_NO_ANSWER = {
    "alert_sent": True,
    "alert_type": "voice_call",
    "alert_kind": "no_answer",
    "risk_level": "UNKNOWN",
    "to": PHONE_CAREGIVER,
    "alert_id": 99,
    "caregiver_call_sid": FULL_SID,
    "message_preview": {"senior_name": SENIOR_NAME, "call_status": "no-answer"},
}


class TestSafeAlertResultForLogging:
    def test_none_returns_none(self):
        assert safe_alert_result_for_logging(None) is None

    # --- safe fields present ---

    def test_alert_sent_present(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        assert result["alert_sent"] is True

    def test_alert_type_present(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        assert result["alert_type"] == "voice_call"

    def test_alert_kind_present(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        assert result["alert_kind"] == "speech_risk"

    def test_risk_level_present(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        assert result["risk_level"] == "RED"

    def test_alert_id_present(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        assert result["alert_id"] == 42

    def test_message_preview_present_flag_true(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        assert result["message_preview_present"] is True

    def test_message_preview_present_flag_false(self):
        result = safe_alert_result_for_logging(ALERT_SKIPPED)
        assert result["message_preview_present"] is False

    # --- sensitive fields masked / excluded ---

    def test_phone_masked(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        assert PHONE_CAREGIVER not in str(result.get("to", ""))
        assert result["to"] is not None  # masked value is still present

    def test_call_sid_masked(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        sid = result.get("caregiver_call_sid", "")
        assert FULL_SID not in sid
        assert sid.startswith("CAe4")

    def test_message_preview_key_absent(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        assert "message_preview" not in result

    def test_senior_name_not_in_output(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        assert SENIOR_NAME not in json.dumps(result)

    def test_transcript_not_in_output(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        assert TRANSCRIPT not in json.dumps(result)

    def test_caregiver_summary_not_in_output(self):
        result = safe_alert_result_for_logging(ALERT_SUCCESS)
        assert CAREGIVER_SUMMARY not in json.dumps(result)

    # --- reason / error handling ---

    def test_skipped_reason_present(self):
        result = safe_alert_result_for_logging(ALERT_SKIPPED)
        assert "reason" in result
        assert "Risk level" in result["reason"]

    def test_failure_error_present(self):
        result = safe_alert_result_for_logging(ALERT_FAILURE)
        assert result.get("error") == "Connection refused"

    # --- no-answer path ---

    def test_no_answer_alert_kind(self):
        result = safe_alert_result_for_logging(ALERT_NO_ANSWER)
        assert result["alert_kind"] == "no_answer"
        assert result["message_preview_present"] is True
        assert SENIOR_NAME not in json.dumps(result)


# ---------------------------------------------------------------------------
# safe_baseline_comparison_for_logging
# ---------------------------------------------------------------------------

COMPARISON_WITH_BASELINE = {
    "has_baseline": True,
    "baseline_sample_id": 7,
    "check_in_id": 55,
    "baseline_transcript": BASELINE_TRANSCRIPT,
    "current_transcript": TRANSCRIPT,
    "baseline_deviation_level": "RED",
    "baseline_word_count": 12,
    "current_word_count": 3,
    "word_count_ratio": 0.25,
    "confidence_delta": 0.4,
    "confidence_drop_detected": True,
    "shorter_response_detected": True,
    "reasons": [
        "Current response is extremely short compared with the captured baseline.",
        "Speech confidence dropped sharply compared with the baseline.",
    ],
}

COMPARISON_NO_BASELINE = {
    "has_baseline": False,
    "baseline_deviation_level": "UNKNOWN",
    "reasons": ["No captured baseline sample exists for this senior yet."],
}


class TestSafeBaselineComparisonForLogging:
    def test_none_returns_none(self):
        assert safe_baseline_comparison_for_logging(None) is None

    def test_transcripts_excluded(self):
        result = safe_baseline_comparison_for_logging(COMPARISON_WITH_BASELINE)
        assert "baseline_transcript" not in result
        assert "current_transcript" not in result
        assert BASELINE_TRANSCRIPT not in json.dumps(result)
        assert TRANSCRIPT not in json.dumps(result)

    def test_safe_fields_present(self):
        result = safe_baseline_comparison_for_logging(COMPARISON_WITH_BASELINE)
        assert result["has_baseline"] is True
        assert result["baseline_deviation_level"] == "RED"
        assert result["baseline_sample_id"] == 7
        assert result["check_in_id"] == 55
        assert result["baseline_word_count"] == 12
        assert result["current_word_count"] == 3
        assert result["word_count_ratio"] == pytest.approx(0.25)
        assert result["confidence_delta"] == pytest.approx(0.4)
        assert result["confidence_drop_detected"] is True
        assert result["shorter_response_detected"] is True

    def test_reason_count_not_text(self):
        result = safe_baseline_comparison_for_logging(COMPARISON_WITH_BASELINE)
        assert result["reason_count"] == 2
        assert "reasons" not in result

    def test_no_baseline_case(self):
        result = safe_baseline_comparison_for_logging(COMPARISON_NO_BASELINE)
        assert result["has_baseline"] is False
        assert result["reason_count"] == 1
        assert "reasons" not in result
