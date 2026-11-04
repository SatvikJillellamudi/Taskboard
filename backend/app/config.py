import os

from dotenv import load_dotenv

load_dotenv()

DEV_SECRET = "dev-only-insecure-secret-change-me-in-production"


def normalize_db_url(url: str) -> str:
    """Hosts hand out postgres:// or postgresql:// URLs; SQLAlchemy needs the driver named."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Settings:
    ENV: str = os.getenv("ENV", "development")
    # SQLite for local dev; a postgresql:// URL (e.g. from Neon) in production
    DATABASE_URL: str = normalize_db_url(os.getenv("DATABASE_URL", "sqlite:///./taskboard.db"))
    JWT_SECRET: str = os.getenv("JWT_SECRET", DEV_SECRET)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    # Comma-separated frontend origins allowed to call the API
    CORS_ORIGINS: list[str] = [o.strip().rstrip("/") for o in
                               os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

    def check_production(self) -> None:
        """Refuse to start in production with settings that would be insecure or lose data."""
        if self.ENV != "production":
            return
        problems = []
        if self.JWT_SECRET == DEV_SECRET or len(self.JWT_SECRET) < 32:
            problems.append("JWT_SECRET must be a random value of at least 32 characters")
        if self.DATABASE_URL.startswith("sqlite"):
            problems.append("DATABASE_URL must point to Postgres (SQLite files are wiped on redeploy)")
        if problems:
            raise RuntimeError("Unsafe production config: " + "; ".join(problems))


settings = Settings()
