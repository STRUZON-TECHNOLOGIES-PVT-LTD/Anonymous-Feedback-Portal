import ipaddress
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import Admin, AdminSession, AuditLog
from app.security import COOKIE_NAME, decode_access_token

_settings = get_settings()


async def get_current_admin(request: Request, db: AsyncSession = Depends(get_db)) -> Admin:
    token = request.cookies.get(COOKIE_NAME)
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if not token:
        raise unauthorized

    claims = decode_access_token(token)
    if not claims:
        raise unauthorized

    row = (
        await db.execute(
            select(Admin, AdminSession)
            .join(AdminSession, AdminSession.admin_id == Admin.id)
            .where(AdminSession.jti == claims["jti"], Admin.username == claims["sub"])
        )
    ).first()
    if not row:
        raise unauthorized

    admin, session = row
    if session.revoked or session.expires_at <= datetime.now(timezone.utc):
        raise unauthorized

    return admin


def _valid_ip(value: str) -> str | None:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


def client_ip(request: Request, trust_proxy_headers: bool, trusted_hops: int = 1) -> str | None:
    """Client IP. With a trusted proxy chain, take the entry `trusted_hops` from
    the RIGHT of X-Forwarded-For (what our own proxy observed); left-most
    entries are client-supplied and spoofable. Falls back to the socket peer."""
    if trust_proxy_headers and trusted_hops > 0:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            parts = [p for p in forwarded.split(",") if p.strip()]
            if len(parts) >= trusted_hops:
                ip = _valid_ip(parts[-trusted_hops])
                if ip:
                    return ip
    return request.client.host if request.client else None


async def audit(db: AsyncSession, request: Request, action: str, username: str | None, resource: str | None = None):
    db.add(
        AuditLog(
            username=username,
            action=action,
            resource=resource,
            ip_address=client_ip(request, _settings.trust_proxy_headers, _settings.trusted_proxy_hops),
        )
    )
    await db.commit()
