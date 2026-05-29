import json
import re
from typing import Any

from app.config import settings


PHONE_PATTERN = re.compile(r"\+\d{8,15}")


# Phone / contact identifiers
SENSITIVE_KEYWORDS = (
    "phone",
    "phone_number",
    "from_number",
    "to_number",
    "caregiver_phone_number",
    "senior_phone_number",
)

# Twilio call/message SIDs
CALL_SID_KEYWORDS = (
    "call_sid",
    "senior_call_sid",
    "caregiver_call_sid",
    "source_call_sid",
    "message_sid",
)

# Spoken transcripts
TRANSCRIPT_KEYWORDS = (
    "transcript",
    "speech_result",
    "source_transcript",
)

# Raw LLM / analysis blobs
RAW_ANALYSIS_KEYWORDS = (
    "raw_analysis",
    "raw_analysis_json",
    "raw_response",
    "raw_response_json",
)

# Senior / caregiver identity
IDENTITY_KEYWORDS = (
    "senior_name",
    "caregiver_name",
)

# Clinical health-context content that may include names or assessments
HEALTH_CONTENT_KEYWORDS = (
    "caregiver_summary",
    "recommended_action",
    "reported_symptoms",
    "symptoms",
    "red_flags",
    "notes",
)

# Full payload / preview blobs
PAYLOAD_KEYWORDS = (
    "message_preview",
    "payload",
)


def _log_pii_enabled() -> bool:
    return bool(getattr(settings, "log_pii", False))


def _log_transcripts_enabled() -> bool:
    return bool(getattr(settings, "log_transcripts", False))


def _log_raw_analysis_enabled() -> bool:
    return bool(getattr(settings, "log_raw_analysis", False))


def mask_phone_number(value: str | None) -> str | None:
    """
    Redacts a phone number while keeping enough shape for debugging.

    Example:
    +19169472666 -> +1******2666
    """

    if value is None:
        return None

    if _log_pii_enabled():
        return value

    text = str(value)

    if len(text) < 6:
        return "[phone hidden]"

    if text.startswith("+") and len(text) >= 8:
        return f"{text[:2]}******{text[-4:]}"

    return f"******{text[-4:]}"


def mask_call_sid(value: str | None) -> str | None:
    """
    Redacts Twilio IDs while keeping first/last characters for correlation.

    Example:
    CA20e9a7d796edb23a3f0c0b5b5e757fdc -> CA20...7fdc
    """

    if value is None:
        return None

    if _log_pii_enabled():
        return value

    text = str(value)

    if len(text) <= 10:
        return "[id hidden]"

    return f"{text[:4]}...{text[-4:]}"


def hide_transcript(value: Any) -> Any:
    if _log_transcripts_enabled():
        return value

    if value is None:
        return None

    text = str(value)

    return {
        "hidden": True,
        "length_chars": len(text),
        "approx_words": len(text.split()),
    }


def hide_raw_analysis(value: Any) -> Any:
    if _log_raw_analysis_enabled():
        return value

    if value is None:
        return None

    return "[raw analysis hidden]"


def redact_string(value: str) -> str:
    """
    Redacts phone numbers that appear inside longer strings.
    """

    if _log_pii_enabled():
        return value

    return PHONE_PATTERN.sub(
        lambda match: mask_phone_number(match.group(0)) or "[phone hidden]",
        value,
    )


def safe_value(key: str, value: Any) -> Any:
    normalized_key = key.lower()

    if any(keyword in normalized_key for keyword in SENSITIVE_KEYWORDS):
        return mask_phone_number(str(value)) if value is not None else None

    if any(keyword in normalized_key for keyword in CALL_SID_KEYWORDS):
        return mask_call_sid(str(value)) if value is not None else None

    if any(keyword in normalized_key for keyword in TRANSCRIPT_KEYWORDS):
        return hide_transcript(value)

    if any(keyword in normalized_key for keyword in RAW_ANALYSIS_KEYWORDS):
        return hide_raw_analysis(value)

    if any(keyword in normalized_key for keyword in IDENTITY_KEYWORDS):
        return value if _log_pii_enabled() else "[name hidden]"

    if any(keyword in normalized_key for keyword in HEALTH_CONTENT_KEYWORDS):
        if _log_pii_enabled():
            return value
        if isinstance(value, list):
            return {"hidden": True, "count": len(value)}
        return "[hidden]"

    if any(keyword in normalized_key for keyword in PAYLOAD_KEYWORDS):
        if _log_pii_enabled():
            return safe_log_object(value)
        return {"present": value is not None}

    return safe_log_object(value)


def safe_log_object(value: Any) -> Any:
    """
    Recursively redacts dictionaries/lists before logging.
    """

    if isinstance(value, dict):
        return {
            key: safe_value(str(key), nested_value)
            for key, nested_value in value.items()
        }

    if isinstance(value, list):
        return [safe_log_object(item) for item in value]

    if isinstance(value, tuple):
        return [safe_log_object(item) for item in value]

    if isinstance(value, str):
        return redact_string(value)

    return value


def safe_json_dumps(value: Any) -> str:
    return json.dumps(
        safe_log_object(value),
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def safe_alert_result_for_logging(
    alert_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """
    Returns a safe subset of an alert result dict for logging.

    Drops message_preview and any raw payload fields.
    Masks phone numbers and call SIDs.
    """

    if alert_result is None:
        return None

    out: dict[str, Any] = {}

    for key in ("alert_sent", "alert_type", "alert_kind", "risk_level", "alert_id", "check_in_id"):
        if key in alert_result:
            out[key] = alert_result[key]

    if "reason" in alert_result:
        out["reason"] = redact_string(str(alert_result["reason"]))

    if "caregiver_call_sid" in alert_result:
        out["caregiver_call_sid"] = mask_call_sid(str(alert_result["caregiver_call_sid"]))

    if "source_call_sid" in alert_result:
        out["source_call_sid"] = mask_call_sid(str(alert_result["source_call_sid"]))

    if "to" in alert_result:
        out["to"] = mask_phone_number(str(alert_result["to"]))

    if "error" in alert_result:
        out["error"] = redact_string(str(alert_result["error"]))

    out["message_preview_present"] = bool(alert_result.get("message_preview"))

    return out


def safe_baseline_comparison_for_logging(
    comparison: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """
    Returns a safe subset of a baseline comparison dict for logging.

    Drops baseline_transcript, current_transcript, and any raw text.
    Keeps numeric metrics and deviation level.
    """

    if comparison is None:
        return None

    out: dict[str, Any] = {}

    for key in (
        "has_baseline",
        "baseline_deviation_level",
        "baseline_sample_id",
        "check_in_id",
        "baseline_word_count",
        "current_word_count",
        "word_count_ratio",
        "confidence_delta",
        "confidence_drop_detected",
        "shorter_response_detected",
    ):
        if key in comparison:
            out[key] = comparison[key]

    reasons = comparison.get("reasons")
    if reasons is not None:
        out["reason_count"] = len(reasons) if isinstance(reasons, list) else 0

    return out


def safe_log_event(title: str, payload: dict[str, Any] | None = None) -> None:
    """
    Standard safe terminal logging helper.
    """

    print(f"\n{title}")
    print("-" * len(title))

    if payload is not None:
        print(safe_json_dumps(payload))


def safe_log_line(label: str, value: Any) -> None:
    """
    Safe one-line logging helper.
    """

    redacted = safe_log_object({label: value})
    print(f"{label}: {redacted[label]}")
