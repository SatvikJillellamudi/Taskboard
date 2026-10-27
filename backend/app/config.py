import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # SQLite for local dev; set DATABASE_URL to a postgresql:// URL in production
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./taskboard.db")
    # Sign tokens with this. MUST be overridden with a long random value in production.
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-only-insecure-secret-change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    # Comma-separated list of frontend origins allowed to call the API
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


settings = Settings()
