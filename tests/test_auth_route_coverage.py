from fastapi.routing import APIRoute, APIWebSocketRoute

from app.main import app
from app.security.basic_auth import _is_protected_path, _is_public_path


def _route_path(route) -> str | None:
    path = getattr(route, "path", None)

    if not isinstance(path, str):
        return None

    return path


def test_all_http_routes_are_public_or_auth_protected():
    unclassified_routes: list[str] = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        path = _route_path(route)

        if path is None:
            continue

        if _is_public_path(path):
            continue

        if _is_protected_path(path):
            continue

        methods = sorted(route.methods or [])

        unclassified_routes.append(f"{','.join(methods)} {path}")

    assert unclassified_routes == []


def test_all_websocket_routes_are_public_or_auth_protected():
    unclassified_routes: list[str] = []

    for route in app.routes:
        if not isinstance(route, APIWebSocketRoute):
            continue

        path = _route_path(route)

        if path is None:
            continue

        if _is_public_path(path):
            continue

        if _is_protected_path(path):
            continue

        unclassified_routes.append(f"WEBSOCKET {path}")

    assert unclassified_routes == []


def test_twilio_routes_are_public_by_design():
    assert _is_public_path("/twilio/voice/ai-check-in")
    assert _is_public_path("/twilio/media/ai-check-in")
    assert _is_public_path("/twilio/status")


def test_sensitive_standalone_routes_are_auth_protected():
    assert _is_protected_path("/support-contacts/1")
    assert _is_protected_path("/heat-settings")
    assert _is_protected_path("/ai-call-sessions/1")
    assert _is_protected_path("/operator-actions/pending")
    assert _is_protected_path("/check-ins/1/review")
    assert _is_protected_path("/scheduler/run-due-checks")
    assert _is_protected_path("/scheduler/run-heat-risk-checks")
    assert _is_protected_path("/ready")