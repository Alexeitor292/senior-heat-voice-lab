import base64

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.security.basic_auth import (
    BasicDashboardAuthMiddleware,
    _credentials_are_valid,
    _is_protected_path,
    _is_public_path,
)


def _basic_auth_header(username: str, password: str) -> dict[str, str]:
    raw = f"{username}:{password}".encode("utf-8")
    encoded = base64.b64encode(raw).decode("utf-8")

    return {
        "Authorization": f"Basic {encoded}",
    }


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(BasicDashboardAuthMiddleware)

    @app.get("/")
    def root():
        return {"ok": True}

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/twilio/test")
    def twilio_test():
        return {"ok": True}

    @app.get("/ui-api/map")
    def ui_api_map():
        return {"ok": True}

    @app.get("/seniors")
    def seniors():
        return {"ok": True}

    @app.get("/operator-actions/pending")
    def operator_actions_pending():
        return {"ok": True}

    @app.get("/check-ins/1/review")
    def check_in_review():
        return {"ok": True}

    @app.get("/ai-call-sessions/1")
    def ai_call_session():
        return {"ok": True}

    @app.get("/scheduler/run-due-checks")
    def scheduler_route():
        return {"ok": True}

    @app.get("/debug/check-ins")
    def debug_check_ins():
        return {"ok": True}

    @app.get("/unprotected-demo")
    def unprotected_demo():
        return {"ok": True}

    return app


def test_public_paths_are_not_protected():
    assert _is_public_path("/")
    assert _is_public_path("/health")
    assert _is_public_path("/docs")
    assert _is_public_path("/docs/oauth2-redirect")
    assert _is_public_path("/openapi.json")
    assert _is_public_path("/twilio/voice/heat-check")


def test_operational_paths_are_protected():
    assert _is_protected_path("/ui")
    assert _is_protected_path("/ui/index.html")
    assert _is_protected_path("/dashboard")
    assert _is_protected_path("/ui-api/map")
    assert _is_protected_path("/seniors")
    assert _is_protected_path("/seniors/1")
    assert _is_protected_path("/calls")
    assert _is_protected_path("/operator-actions")
    assert _is_protected_path("/operator-actions/pending")
    assert _is_protected_path("/check-ins/1/review")
    assert _is_protected_path("/schedules")
    assert _is_protected_path("/scheduler/run-due-checks")
    assert _is_protected_path("/operational-status")
    assert _is_protected_path("/debug/check-ins")
    assert _is_protected_path("/ai-call-sessions/1")
    assert _is_protected_path("/ai-call-sessions/1/turns")
    assert _is_protected_path("/ai-call-sessions/1/complete")


def test_prefix_matching_does_not_overmatch_similar_paths():
    assert not _is_public_path("/twilio-malicious")
    assert not _is_public_path("/healthcheck")
    assert not _is_protected_path("/seniors-extra")
    assert not _is_protected_path("/ui-api-extra")
    assert not _is_protected_path("/debugger")
    assert not _is_protected_path("/ai-call-sessions-extra")


def test_credentials_are_valid_with_expected_admin_credentials(monkeypatch):
    monkeypatch.setattr(
        "app.security.basic_auth.settings.admin_username",
        "admin",
    )
    monkeypatch.setattr(
        "app.security.basic_auth.settings.admin_password",
        "change-me-local-dev",
    )

    header = _basic_auth_header("admin", "change-me-local-dev")["Authorization"]

    assert _credentials_are_valid(header)


def test_credentials_reject_missing_or_invalid_values(monkeypatch):
    monkeypatch.setattr(
        "app.security.basic_auth.settings.admin_username",
        "admin",
    )
    monkeypatch.setattr(
        "app.security.basic_auth.settings.admin_password",
        "change-me-local-dev",
    )

    assert not _credentials_are_valid(None)
    assert not _credentials_are_valid("")
    assert not _credentials_are_valid("Bearer token")
    assert not _credentials_are_valid("Basic not-base64")
    assert not _credentials_are_valid(
        _basic_auth_header("admin", "wrong-password")["Authorization"]
    )
    assert not _credentials_are_valid(
        _basic_auth_header("wrong-user", "change-me-local-dev")["Authorization"]
    )


def test_public_routes_do_not_require_basic_auth(monkeypatch):
    monkeypatch.setattr(
        "app.security.basic_auth.settings.dashboard_auth_enabled",
        True,
    )
    monkeypatch.setattr(
        "app.security.basic_auth.settings.admin_username",
        "admin",
    )
    monkeypatch.setattr(
        "app.security.basic_auth.settings.admin_password",
        "change-me-local-dev",
    )

    client = TestClient(_build_test_app())

    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
    assert client.get("/twilio/test").status_code == 200


def test_protected_routes_require_basic_auth(monkeypatch):
    monkeypatch.setattr(
        "app.security.basic_auth.settings.dashboard_auth_enabled",
        True,
    )
    monkeypatch.setattr(
        "app.security.basic_auth.settings.admin_username",
        "admin",
    )
    monkeypatch.setattr(
        "app.security.basic_auth.settings.admin_password",
        "change-me-local-dev",
    )

    client = TestClient(_build_test_app())

    protected_paths = [
        "/ui-api/map",
        "/seniors",
        "/operator-actions/pending",
        "/check-ins/1/review",
        "/ai-call-sessions/1",
        "/scheduler/run-due-checks",
        "/debug/check-ins",
    ]

    for path in protected_paths:
        response = client.get(path)

        assert response.status_code == 401
        assert response.text == "Authentication required."
        assert (
            response.headers["WWW-Authenticate"]
            == 'Basic realm="Senior Heat Voice Lab"'
        )


def test_protected_routes_accept_valid_basic_auth(monkeypatch):
    monkeypatch.setattr(
        "app.security.basic_auth.settings.dashboard_auth_enabled",
        True,
    )
    monkeypatch.setattr(
        "app.security.basic_auth.settings.admin_username",
        "admin",
    )
    monkeypatch.setattr(
        "app.security.basic_auth.settings.admin_password",
        "change-me-local-dev",
    )

    client = TestClient(_build_test_app())
    headers = _basic_auth_header("admin", "change-me-local-dev")

    protected_paths = [
        "/ui-api/map",
        "/seniors",
        "/operator-actions/pending",
        "/check-ins/1/review",
        "/ai-call-sessions/1",
        "/scheduler/run-due-checks",
        "/debug/check-ins",
    ]

    for path in protected_paths:
        response = client.get(path, headers=headers)

        assert response.status_code == 200
        assert response.json() == {"ok": True}


def test_unlisted_paths_remain_unprotected(monkeypatch):
    monkeypatch.setattr(
        "app.security.basic_auth.settings.dashboard_auth_enabled",
        True,
    )

    client = TestClient(_build_test_app())

    response = client.get("/unprotected-demo")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_options_requests_bypass_basic_auth(monkeypatch):
    monkeypatch.setattr(
        "app.security.basic_auth.settings.dashboard_auth_enabled",
        True,
    )

    client = TestClient(_build_test_app())

    response = client.options("/ui-api/map")

    assert response.status_code in {200, 405}
    assert response.status_code != 401


def test_auth_can_be_disabled_for_local_development(monkeypatch):
    monkeypatch.setattr(
        "app.security.basic_auth.settings.dashboard_auth_enabled",
        False,
    )

    client = TestClient(_build_test_app())

    response = client.get("/ui-api/map")

    assert response.status_code == 200
    assert response.json() == {"ok": True}