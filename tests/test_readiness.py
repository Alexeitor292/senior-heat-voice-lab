from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text


from app.db.database import engine


def _current_migration_head() -> str:
    config = Config("alembic.ini")
    config.set_main_option("script_location", "migrations")
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()

    assert len(heads) == 1

    return heads[0]


def _clear_alembic_version_table() -> None:
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))


def _stamp_test_database_head() -> None:
    head = _current_migration_head()

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS alembic_version "
                "(version_num VARCHAR(32) NOT NULL)"
            )
        )
        connection.execute(text("DELETE FROM alembic_version"))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:head)"),
            {
                "head": head,
            },
        )


def test_health_check_stays_public_and_lightweight(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_readiness_requires_auth(client):
    response = client.get("/ready")

    assert response.status_code == 401
    assert response.text == "Authentication required."


def test_readiness_reports_not_ready_when_migrations_are_not_stamped(
    client,
    auth_headers,
):
    _clear_alembic_version_table()

    response = client.get(
        "/ready",
        headers=auth_headers,
    )

    assert response.status_code == 503

    payload = response.json()

    assert payload["status"] == "not_ready"
    assert payload["ready"] is False
    assert payload["checks"]["database"]["ok"] is True
    assert payload["checks"]["migrations"]["ok"] is False
    assert payload["checks"]["migrations"]["current_heads"] == []
    assert payload["checks"]["migrations"]["expected_heads"]


def test_readiness_reports_ready_when_database_is_at_migration_head(
    client,
    auth_headers,
):
    _clear_alembic_version_table()
    _stamp_test_database_head()

    response = client.get(
        "/ready",
        headers=auth_headers,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ready"
    assert payload["ready"] is True
    assert payload["checks"]["database"]["ok"] is True
    assert payload["checks"]["migrations"]["ok"] is True
    assert payload["checks"]["migrations"]["current_heads"] == payload["checks"][
        "migrations"
    ]["expected_heads"]