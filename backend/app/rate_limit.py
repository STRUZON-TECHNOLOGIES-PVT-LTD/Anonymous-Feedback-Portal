from slowapi import Limiter

from app.config import get_settings
from app.deps import client_ip

settings = get_settings()


def _rate_limit_key(request) -> str:
    """IP used for rate-limit bucketing.

    Mirrors ``app.deps.client_ip`` (which keys stored submissions) so the
    limiter and the recorded IP agree: honour ``X-Forwarded-For`` only when
    ``TRUST_PROXY_HEADERS`` is set, and fall back to a stable sentinel when no
    client address is available (rate limit applies, just not per-IP).
    """
    ip = client_ip(request, settings.trust_proxy_headers)
    return ip or "unknown"


limiter = Limiter(key_func=_rate_limit_key)