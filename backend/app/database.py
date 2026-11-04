from sqlalchemy import event
from sqlmodel import SQLModel, Session, create_engine

from .config import settings

IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")


def enforce_sqlite_foreign_keys(engine) -> None:
    """SQLite ignores foreign keys unless asked. Turn them on so local dev and tests
    reject the same invalid writes Postgres does in production."""
    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


engine = create_engine(
    settings.DATABASE_URL,
    # SQLite needs this to be shared across FastAPI's threads
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    # Check a pooled connection is alive before using it. Serverless Postgres (Neon) closes
    # idle connections, so without this the first request after a quiet period would fail.
    pool_pre_ping=True,
)
if IS_SQLITE:
    enforce_sqlite_foreign_keys(engine)


def init_db() -> None:
    """Local SQLite: create tables directly for convenience.
    Postgres: the schema is managed by Alembic migrations (alembic upgrade head)."""
    if IS_SQLITE:
        from . import models  # noqa: F401  (registers the tables)
        SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency: one database session per request."""
    with Session(engine) as session:
        yield session
