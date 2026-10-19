"""Application configuration with sensible dev defaults."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql://afterlight:afterlight@localhost:5432/afterlight"

    # Security
    secret_key: str = "dev-secret-change-me-in-production"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    refresh_token_expire_days: int = 30
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536  # 64 MB
    argon2_parallelism: int = 4

    # Encryption
    # Client-side encryption: server never sees plaintext or master password.
    # These are for server-side envelope encryption of the user's key encryption key (KEK).
    encryption_key: str = "base64-encoded-32-byte-key-change-me"

    # Dead Man's Switch defaults
    default_check_in_interval_days: int = 30
    default_grace_period_days: int = 14
    max_check_in_interval_days: int = 365
    min_check_in_interval_days: int = 7

    # Email (for check-in reminders and legacy messages)
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@afterlight.io"
    smtp_use_tls: bool = True

    # App
    app_name: str = "Afterlight"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60


settings = Settings()
