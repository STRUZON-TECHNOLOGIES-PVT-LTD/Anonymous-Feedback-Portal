from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolved relative to this file (backend/app/config.py -> backend/.env) rather
# than the process's current working directory, so `.env` loads the same way
# whether the app is started from `backend/` or from elsewhere (e.g. a launcher
# that doesn't set cwd, a systemd unit, etc).
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8")

    database_url: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    cookie_secure: bool = False

    admin_bootstrap_username: str | None = None
    admin_bootstrap_password: str | None = None

    frontend_origins: str = "http://localhost:5173"

    submit_rate_limit: str = "5/hour"
    login_rate_limit: str = "10/minute"
    trust_proxy_headers: bool = False

    @property
    def frontend_origin_list(self) -> list[str]:
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
