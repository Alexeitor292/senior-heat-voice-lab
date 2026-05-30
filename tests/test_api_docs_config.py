from fastapi import FastAPI

from app.config import Settings


BASE_SETTINGS = {
    "twilio_account_sid": "ACtest00000000000000000000000000000",
    "twilio_auth_token": "test_auth_token",
    "twilio_phone_number": "+15550000000",
    "test_phone_number": "+15551111111",
    "public_base_url": "https://test.example.com",
}


def _build_docs_test_app(settings: Settings) -> FastAPI:
    return FastAPI(
        title=settings.app_name,
        docs_url="/docs" if settings.expose_api_docs else None,
        redoc_url="/redoc" if settings.expose_api_docs else None,
        openapi_url="/openapi.json" if settings.expose_api_docs else None,
    )


def test_api_docs_are_enabled_when_configured():
    settings = Settings(
        **BASE_SETTINGS,
        app_env="development",
        expose_api_docs=True,
    )

    app = _build_docs_test_app(settings)

    paths = {route.path for route in app.routes}

    assert "/docs" in paths
    assert "/redoc" in paths
    assert "/openapi.json" in paths


def test_api_docs_are_disabled_when_configured():
    settings = Settings(
        **BASE_SETTINGS,
        app_env="development",
        expose_api_docs=False,
    )

    app = _build_docs_test_app(settings)

    paths = {route.path for route in app.routes}

    assert "/docs" not in paths
    assert "/redoc" not in paths
    assert "/openapi.json" not in paths