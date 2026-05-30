from app.config import Settings


def test_cors_allowed_origins_list_parses_comma_separated_values():
    settings = Settings(
        twilio_account_sid="ACtest00000000000000000000000000000",
        twilio_auth_token="test_auth_token",
        twilio_phone_number="+15550000000",
        test_phone_number="+15551111111",
        public_base_url="https://test.example.com",
        cors_allowed_origins=(
            "http://localhost:3000, "
            "http://127.0.0.1:3000,"
            "https://frontend.example.com"
        ),
    )

    assert settings.cors_allowed_origins_list() == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://frontend.example.com",
    ]


def test_cors_allowed_origins_list_ignores_empty_values():
    settings = Settings(
        twilio_account_sid="ACtest00000000000000000000000000000",
        twilio_auth_token="test_auth_token",
        twilio_phone_number="+15550000000",
        test_phone_number="+15551111111",
        public_base_url="https://test.example.com",
        cors_allowed_origins="http://localhost:3000,, ,https://frontend.example.com",
    )

    assert settings.cors_allowed_origins_list() == [
        "http://localhost:3000",
        "https://frontend.example.com",
    ]