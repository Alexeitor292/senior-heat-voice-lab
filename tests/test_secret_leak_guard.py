from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_TRACKED_FILENAMES = {
    ".env",
    ".env.local",
    "frontend/.env.local",
}

FORBIDDEN_TRACKED_SUFFIXES = (
    ".env.local",
    ".env.production",
    ".env.prod",
    ".env.staging",
)

IGNORED_PATH_PREFIXES = (
    ".git/",
    ".github/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".venv/",
    "venv/",
    "node_modules/",
    "frontend/node_modules/",
    "frontend/.next/",
    "data/",
)

IGNORED_EXACT_PATHS = {
    # These tests intentionally contain fake production-looking values
    # to verify config validation behavior.
    "tests/test_production_config_safety.py",
    "tests/test_secret_leak_guard.py",
}

PLACEHOLDER_VALUE_MARKERS = (
    "example",
    "your_",
    "your-",
    "paste_",
    "paste-",
    "replace",
    "changeme",
    "change-me-local-dev",
    "test_auth_token",
    "strong-random",
    "generated_random",
    "local-dev",
    "<",
    ">",
    "***",
)

ALLOWLIST_VALUES = {
    "ACtest00000000000000000000000000000",
    "sk-test",
    "test.example.com",
}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "OpenAI API key",
        re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b"),
    ),
    (
        "Twilio Account SID",
        re.compile(r"\bAC[0-9a-fA-F]{32}\b"),
    ),
    (
        "Twilio Auth Token assignment",
        re.compile(r"(?im)^\s*TWILIO_AUTH_TOKEN\s*=\s*(.+?)\s*$"),
    ),
    (
        "OpenAI API key assignment",
        re.compile(r"(?im)^\s*OPENAI_API_KEY\s*=\s*(.+?)\s*$"),
    ),
    (
        "Admin password assignment",
        re.compile(r"(?im)^\s*ADMIN_PASSWORD\s*=\s*(.+?)\s*$"),
    ),
    (
        "AI stream token secret assignment",
        re.compile(r"(?im)^\s*AI_STREAM_TOKEN_SECRET\s*=\s*(.+?)\s*$"),
    ),
)


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    return [
        line.strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def _should_scan(path: str) -> bool:
    if path in IGNORED_EXACT_PATHS:
        return False

    if path.startswith(IGNORED_PATH_PREFIXES):
        return False

    if path.endswith(
        (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".ico",
            ".pdf",
            ".db",
            ".sqlite",
            ".sqlite3",
            ".lock",
        )
    ):
        return False

    return True


def _extract_assignment_value(line: str) -> str:
    if "=" not in line:
        return line.strip()

    return line.split("=", 1)[1].strip().strip('"').strip("'")


def _is_placeholder_or_allowlisted(line: str) -> bool:
    value = _extract_assignment_value(line)
    value_lower = value.lower()

    if not value:
        return True

    if value in ALLOWLIST_VALUES:
        return True

    if set(value) == {"*"}:
        return True

    return any(marker in value_lower for marker in PLACEHOLDER_VALUE_MARKERS)


def test_no_forbidden_env_files_are_tracked():
    tracked = set(_tracked_files())

    forbidden = sorted(
        path
        for path in tracked
        if path in FORBIDDEN_TRACKED_FILENAMES
        or path.endswith(FORBIDDEN_TRACKED_SUFFIXES)
    )

    assert forbidden == []


def test_no_obvious_secrets_are_committed():
    findings: list[str] = []

    for tracked_path in _tracked_files():
        if not _should_scan(tracked_path):
            continue

        path = REPO_ROOT / tracked_path

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        lines = content.splitlines()

        for secret_name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(content):
                line_number = content.count("\n", 0, match.start()) + 1
                line = lines[line_number - 1]

                if _is_placeholder_or_allowlisted(line):
                    continue

                findings.append(
                    f"{tracked_path}:{line_number}: possible {secret_name}"
                )

    assert findings == []