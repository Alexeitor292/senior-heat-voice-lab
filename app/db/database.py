from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_parent_dir_exists():
    """
    If using local SQLite, make sure the ./data folder exists.
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
    else {}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def init_db():
    """
    Creates database tables if they do not exist.

    For now this is enough for local dev.
    Later, use Alembic migrations.
    """

    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)