from __future__ import annotations

from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.db.database import engine


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    repo_root = _repo_root()
    config = Config(str(repo_root / "alembic.ini"))
    config.set_main_option("script_location", str(repo_root / "migrations"))

    return config


def _expected_migration_heads() -> tuple[str, ...]:
    script = ScriptDirectory.from_config(_alembic_config())

    return tuple(script.get_heads())


def _current_database_heads(connection) -> tuple[str, ...]:
    context = MigrationContext.configure(connection)

    return tuple(context.get_current_heads())


def get_readiness() -> dict[str, Any]:
    checks: dict[str, Any] = {
        "database": {
            "ok": False,
        },
        "migrations": {
            "ok": False,
            "current_heads": [],
            "expected_heads": [],
        },
    }

    expected_heads: tuple[str, ...] = tuple()

    try:
        expected_heads = _expected_migration_heads()
        checks["migrations"]["expected_heads"] = list(expected_heads)
    except Exception as exc:
        checks["migrations"]["error"] = repr(exc)

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            checks["database"]["ok"] = True

            current_heads = _current_database_heads(connection)
            checks["migrations"]["current_heads"] = list(current_heads)

            checks["migrations"]["ok"] = (
                bool(expected_heads)
                and set(current_heads) == set(expected_heads)
            )

    except Exception as exc:
        checks["database"]["error"] = repr(exc)

    ready = bool(checks["database"]["ok"] and checks["migrations"]["ok"])

    return {
        "status": "ready" if ready else "not_ready",
        "ready": ready,
        "checks": checks,
    }