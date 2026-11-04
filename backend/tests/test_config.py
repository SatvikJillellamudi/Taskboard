import pytest

from app.config import DEV_SECRET, Settings, normalize_db_url


def test_normalizes_hosted_postgres_urls():
    assert normalize_db_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize_db_url("postgresql://u:p@h/db?sslmode=require") == \
        "postgresql+psycopg://u:p@h/db?sslmode=require"
    assert normalize_db_url("sqlite:///./x.db") == "sqlite:///./x.db"


def make(env, secret, url):
    s = Settings()
    s.ENV, s.JWT_SECRET, s.DATABASE_URL = env, secret, url
    return s


def test_production_rejects_dev_secret():
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        make("production", DEV_SECRET, "postgresql+psycopg://h/db").check_production()


def test_production_rejects_sqlite():
    with pytest.raises(RuntimeError, match="Postgres"):
        make("production", "x" * 48, "sqlite:///./taskboard.db").check_production()


def test_production_accepts_safe_config():
    make("production", "x" * 48, "postgresql+psycopg://h/db").check_production()


def test_development_is_lenient():
    make("development", DEV_SECRET, "sqlite:///./taskboard.db").check_production()
