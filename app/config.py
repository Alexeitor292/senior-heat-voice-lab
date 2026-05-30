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

    database_url: str = "sqlite:///./data/senior_heat_voice_lab.db"

    scheduler_poll_seconds: int = 60

    heat_risk_provider: str = "manual"
    manual_heat_risk_value: int = 2
    nws_user_agent: str = "SeniorHeatVoiceLab/0.1 local-dev"

    dashboard_auth_enabled: bool = True
    admin_username: str = "admin"
    admin_password: str = "change-me-local-dev"

    twilio_signature_validation_enabled: bool = True

    log_pii: bool = False
    log_transcripts: bool = False
    log_raw_analysis: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()