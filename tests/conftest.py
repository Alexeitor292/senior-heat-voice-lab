import base64
import os

import pytest
from fastapi.testclient import TestClient

# Provide minimal required settings so pydantic-settings can load without a real .env.
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACtest00000000000000000000000000000")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test_auth_token_00000000000000000000")
os.environ.setdefault("TWILIO_PHONE_NUMBER", "+15550000000")
os.environ.setdefault("TEST_PHONE_NUMBER", "+15551111111")
os.environ.setdefault("PUBLIC_BASE_URL", "https://test.example.com")

# Use an isolated local test DB unless CI or the developer explicitly provides one.
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_senior_heat_voice_lab.db")
os.environ.setdefault("AUTO_CREATE_DB_TABLES", "true")

os.environ.setdefault("HEAT_RISK_PROVIDER", "manual")
os.environ.setdefault("MANUAL_HEAT_RISK_VALUE", "2")

os.environ.setdefault("DASHBOARD_AUTH_ENABLED", "true")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "change-me-local-dev")

os.environ.setdefault("TWILIO_SIGNATURE_VALIDATION_ENABLED", "true")
os.environ.setdefault("OPENAI_REALTIME_ENABLED", "false")

os.environ.setdefault("LOG_PII", "false")
os.environ.setdefault("LOG_TRANSCRIPTS", "false")
os.environ.setdefault("LOG_RAW_ANALYSIS", "false")

from app.db import models  # noqa: E402,F401
from app.db.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    raw = b"admin:change-me-local-dev"
    encoded = base64.b64encode(raw).decode("utf-8")

    return {
        "Authorization": f"Basic {encoded}",
    }