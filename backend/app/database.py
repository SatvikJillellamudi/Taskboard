from sqlmodel import SQLModel, Session, create_engine

from .config import settings

# SQLite needs this flag to be used across FastAPI's threads; Postgres does not
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)


def init_db() -> None:
    # Creates tables if missing. We will switch to Alembic migrations before deploying.
    from . import models  # noqa: F401  (registers the tables)
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency: one database session per request."""
    with Session(engine) as session:
        yield session
