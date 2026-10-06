from slowapi import Limiter
from starlette.requests import Request

from app.config import get_settings
from app.deps import client_ip

_settings = get_settings()


def _key(request: Request) -> str:
    # Same trust rules as the IP stored on submissions, so the limiter can't be
    # bypassed via a spoofed X-Forwarded-For nor collapse all users to one proxy IP.
    return client_ip(request, _settings.trust_proxy_headers, _settings.trusted_proxy_hops) or "unknown"


limiter = Limiter(key_func=_key)
