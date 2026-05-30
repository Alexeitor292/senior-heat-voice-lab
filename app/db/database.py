from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_parent_dir_exists() -> None:
    """
    If using local SQLite, make sure the parent folder exists.

    This does not create database tables. It only ensures paths like ./data/
    exist before SQLite tries to open the file.
    """

    database_url = settings.database_url

    if not database_url.startswith("sqlite:///"):
        return

    sqlite_path = database_url.replace("sqlite:///", "")

    if sqlite_path.startswith("./"):
        sqlite_path = sqlite_path[2:]

    db_path = Path(sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_parent_dir_exists()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def init_db() -> None:
    """
    Initializes database access at app startup.

    Alembic migrations are now the default schema-management path.

    Set AUTO_CREATE_DB_TABLES=true only for local throwaway development
    environments where automatic SQLAlchemy create_all behavior is desired.
    Do not use AUTO_CREATE_DB_TABLES=true in production.
    """

    if not settings.auto_create_db_tables:
        print(
            "Database auto-create disabled. "
            "Use `python -m alembic upgrade head` to apply migrations."
        )
        return

    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("Database tables auto-created from SQLAlchemy metadata.")