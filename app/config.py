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

    database_url: str = "sqlite:///./data/senior_heat_voice_lab.db"

    scheduler_poll_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()