from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolved relative to this file (backend/app/config.py -> backend/.env) rather
# than the process's current working directory, so `.env` loads the same way
# whether the app is started from `backend/` or from elsewhere (e.g. a launcher
# that doesn't set cwd, a systemd unit, etc).
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8")

    # "production" (default, secure-by-default) enforces strong secrets, Secure
    # cookies and disables /docs. Set ENVIRONMENT=development for local work.
    environment: str = "production"

    database_url: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    cookie_secure: bool = False

    admin_bootstrap_username: str | None = None
    admin_bootstrap_password: str | None = None

    frontend_origins: str = "http://localhost:5173"

    submit_rate_limit: str = "5/hour"
    login_rate_limit: str = "5/minute"
    login_max_failed_attempts: int = 5
    login_lockout_minutes: int = 15

    # Only enable behind a reverse proxy that APPENDS the real client IP to
    # X-Forwarded-For. `trusted_proxy_hops` = number of proxies you control; the
    # client IP is taken that many entries from the right (never the left-most,
    # which is attacker-controlled).
    trust_proxy_headers: bool = False
    trusted_proxy_hops: int = 1

    # Proof-of-work on public submissions (leading zero bits of sha256).
    pow_difficulty_bits: int = 16
    pow_ttl_seconds: int = 600

    max_body_bytes: int = 65536

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        problems: list[str] = []
        if len(self.jwt_secret) < 32 or "change-this" in self.jwt_secret.lower():
            problems.append("JWT_SECRET must be >= 32 chars and not a placeholder")
        if self.admin_bootstrap_username and self.admin_bootstrap_password:
            if len(self.admin_bootstrap_password) < 12 or "changeme" in self.admin_bootstrap_password.lower():
                problems.append("ADMIN_BOOTSTRAP_PASSWORD must be >= 12 chars and not a placeholder")
        if self.is_production and not self.cookie_secure:
            problems.append("COOKIE_SECURE must be true when ENVIRONMENT=production")
        if problems and self.is_production:
            raise ValueError("Insecure configuration: " + "; ".join(problems))
        if problems:
            import warnings

            warnings.warn("INSECURE DEV CONFIG: " + "; ".join(problems), stacklevel=2)
        return self

    @property
    def frontend_origin_list(self) -> list[str]:
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
