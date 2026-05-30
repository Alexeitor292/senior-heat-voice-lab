import pytest
from pydantic import ValidationError

from app.config import Settings


BASE_SETTINGS = {
    "twilio_account_sid": "ACtest00000000000000000000000000000",
    "twilio_auth_token": "test_auth_token",
    "twilio_phone_number": "+15550000000",
    "test_phone_number": "+15551111111",
    "public_base_url": "https://test.example.com",
}


def test_development_config_allows_local_defaults():
    settings = Settings(
        **BASE_SETTINGS,
        app_env="development",
        admin_username="admin",
        admin_password="change-me-local-dev",
        ai_stream_token_secret=None,
        expose_api_docs=True,
    )

    assert settings.app_env == "development"
    assert settings.admin_password == "change-me-local-dev"
    assert settings.expose_api_docs is True


def test_production_config_rejects_local_defaults():
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            **BASE_SETTINGS,
            app_env="production",
            admin_username="admin",
            admin_password="change-me-local-dev",
            ai_stream_token_secret=None,
            expose_api_docs=True,
        )

    message = str(exc_info.value)

    assert "ADMIN_PASSWORD must not use the local development default" in message
    assert "ADMIN_USERNAME should not use the local development default" in message
    assert "AI_STREAM_TOKEN_SECRET must be set in production" in message
    assert "EXPOSE_API_DOCS must be false in production" in message


def test_production_config_rejects_disabled_security_controls():
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            **BASE_SETTINGS,
            app_env="production",
            admin_username="seniorcare-admin",
            admin_password="strong-random-production-password",
            ai_stream_token_secret="strong-random-stream-secret",
            dashboard_auth_enabled=False,
            twilio_signature_validation_enabled=False,
            auto_create_db_tables=True,
            expose_api_docs=False,
            log_pii=True,
            log_transcripts=True,
            log_raw_analysis=True,
        )

    message = str(exc_info.value)

    assert "DASHBOARD_AUTH_ENABLED must be true in production" in message
    assert "TWILIO_SIGNATURE_VALIDATION_ENABLED must be true in production" in message
    assert "AUTO_CREATE_DB_TABLES must be false in production" in message
    assert "LOG_PII must be false in production" in message
    assert "LOG_TRANSCRIPTS must be false in production" in message
    assert "LOG_RAW_ANALYSIS must be false in production" in message


def test_production_config_rejects_enabled_api_docs():
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            **BASE_SETTINGS,
            app_env="production",
            admin_username="seniorcare-admin",
            admin_password="strong-random-production-password",
            ai_stream_token_secret="strong-random-stream-secret",
            expose_api_docs=True,
        )

    message = str(exc_info.value)

    assert "EXPOSE_API_DOCS must be false in production" in message


def test_production_config_rejects_wildcard_cors_with_credentials():
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            **BASE_SETTINGS,
            app_env="production",
            admin_username="seniorcare-admin",
            admin_password="strong-random-production-password",
            ai_stream_token_secret="strong-random-stream-secret",
            expose_api_docs=False,
            cors_allowed_origins="*",
        )

    message = str(exc_info.value)

    assert "CORS_ALLOWED_ORIGINS must not include '*'" in message


def test_production_config_accepts_hardened_settings():
    settings = Settings(
        **BASE_SETTINGS,
        app_env="production",
        admin_username="seniorcare-admin",
        admin_password="strong-random-production-password",
        ai_stream_token_secret="strong-random-stream-secret",
        auto_create_db_tables=False,
        dashboard_auth_enabled=True,
        twilio_signature_validation_enabled=True,
        expose_api_docs=False,
        log_pii=False,
        log_transcripts=False,
        log_raw_analysis=False,
        cors_allowed_origins="https://seniorcare.example.com",
    )

    assert settings.app_env == "production"
    assert settings.auto_create_db_tables is False
    assert settings.dashboard_auth_enabled is True
    assert settings.twilio_signature_validation_enabled is True
    assert settings.expose_api_docs is False
    assert settings.cors_allowed_origins_list() == [
        "https://seniorcare.example.com"
    ]