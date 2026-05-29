import os

# Provide minimal required settings so pydantic-settings can load without a real .env.
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACtest00000000000000000000000000000")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test_auth_token_00000000000000000000")
os.environ.setdefault("TWILIO_PHONE_NUMBER", "+15550000000")
os.environ.setdefault("TEST_PHONE_NUMBER", "+15551111111")
os.environ.setdefault("PUBLIC_BASE_URL", "https://test.example.com")
os.environ.setdefault("LOG_PII", "false")
os.environ.setdefault("LOG_TRANSCRIPTS", "false")
os.environ.setdefault("LOG_RAW_ANALYSIS", "false")
