from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Senior Heat Voice Lab"
    app_env: str = "development"

    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    test_phone_number: str
    public_base_url: str

    caregiver_test_phone_number: str | None = None

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    openai_realtime_enabled: bool = False
    openai_realtime_model: str = "gpt-realtime-2"
    openai_realtime_voice: str = "marin"

    ai_stream_token_secret: str | None = None
    ai_stream_token_ttl_seconds: int = 300

    database_url: str = "sqlite:///./data/senior_heat_voice_lab.db"
    auto_create_db_tables: bool = False

    scheduler_poll_seconds: int = 60

    heat_risk_provider: str = "manual"
    manual_heat_risk_value: int = 2
    nws_user_agent: str = "SeniorHeatVoiceLab/0.1 local-dev"

    dashboard_auth_enabled: bool = True
    admin_username: str = "admin"
    admin_password: str = "change-me-local-dev"

    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    twilio_signature_validation_enabled: bool = True

    log_pii: bool = False
    log_transcripts: bool = False
    log_raw_analysis: bool = False

    def cors_allowed_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        production_envs = {"production", "prod"}

        if self.app_env.lower().strip() not in production_envs:
            return self

        errors: list[str] = []

        if self.admin_password == "change-me-local-dev":
            errors.append(
                "ADMIN_PASSWORD must not use the local development default in production."
            )

        if self.admin_username == "admin":
            errors.append(
                "ADMIN_USERNAME should not use the local development default in production."
            )

        if self.auto_create_db_tables:
            errors.append(
                "AUTO_CREATE_DB_TABLES must be false in production. Use Alembic migrations."
            )

        if not self.dashboard_auth_enabled:
            errors.append(
                "DASHBOARD_AUTH_ENABLED must be true in production until real user auth replaces it."
            )

        if not self.twilio_signature_validation_enabled:
            errors.append(
                "TWILIO_SIGNATURE_VALIDATION_ENABLED must be true in production."
            )

        if not self.ai_stream_token_secret:
            errors.append(
                "AI_STREAM_TOKEN_SECRET must be set in production."
            )

        if self.log_pii:
            errors.append(
                "LOG_PII must be false in production."
            )

        if self.log_transcripts:
            errors.append(
                "LOG_TRANSCRIPTS must be false in production."
            )

        if self.log_raw_analysis:
            errors.append(
                "LOG_RAW_ANALYSIS must be false in production."
            )

        if "*" in self.cors_allowed_origins_list():
            errors.append(
                "CORS_ALLOWED_ORIGINS must not include '*' in production."
            )

        if errors:
            joined_errors = "\n- ".join(errors)
            raise ValueError(
                "Unsafe production configuration detected:\n"
                f"- {joined_errors}"
            )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()