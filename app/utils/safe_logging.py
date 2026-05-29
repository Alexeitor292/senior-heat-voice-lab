import json
import re
from typing import Any

from app.config import settings


PHONE_PATTERN = re.compile(r"\+\d{8,15}")


SENSITIVE_KEYWORDS = (
    "phone",
    "phone_number",
    "from_number",
    "to_number",
    "caregiver_phone_number",
    "senior_phone_number",
)

CALL_SID_KEYWORDS = (
    "call_sid",
    "senior_call_sid",
    "caregiver_call_sid",
    "source_call_sid",
    "message_sid",
)

TRANSCRIPT_KEYWORDS = (
    "transcript",
    "speech_result",
    "source_transcript",
)

RAW_ANALYSIS_KEYWORDS = (
    "raw_analysis",
    "raw_analysis_json",
    "raw_response",
    "raw_response_json",
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

    if settings.log_pii:
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

    if settings.log_pii:
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