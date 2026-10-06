import hmac
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

COOKIE_NAME = "admin_session"

# Verified against when the username doesn't exist, so response time doesn't
# reveal which usernames are valid.
_DUMMY_HASH = pwd_context.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def verify_dummy_password(password: str) -> None:
    pwd_context.verify(password, _DUMMY_HASH)


def create_access_token(username: str) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    jti = secrets.token_urlsafe(24)
    payload = {"sub": username, "exp": expire, "jti": jti}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), jti, expire


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "jti"]},
        )
    except jwt.PyJWTError:
        return None


# ---------- Proof-of-work challenge (stateless, HMAC-signed) ----------
def _pow_sig(salt: str, exp: int, bits: int) -> str:
    msg = f"{salt}.{exp}.{bits}".encode()
    return hmac.new(settings.jwt_secret.encode(), msg, hashlib.sha256).hexdigest()


def new_pow_challenge() -> dict:
    salt = secrets.token_hex(16)
    exp = int(time.time()) + settings.pow_ttl_seconds
    bits = settings.pow_difficulty_bits
    return {"salt": salt, "exp": exp, "bits": bits, "sig": _pow_sig(salt, exp, bits)}


_used_pow: dict[str, int] = {}  # salt -> exp (per-process replay guard)


def verify_pow(salt: str, exp: int, bits: int, sig: str, nonce: str) -> bool:
    now = int(time.time())
    if exp < now or bits != settings.pow_difficulty_bits:
        return False
    if not hmac.compare_digest(sig, _pow_sig(salt, exp, bits)):
        return False
    if len(nonce) > 32:
        return False
    digest = hashlib.sha256(f"{salt}{nonce}".encode()).digest()
    if int.from_bytes(digest, "big") >> (256 - bits) != 0:
        return False
    for k in [k for k, v in _used_pow.items() if v < now]:
        del _used_pow[k]
    if salt in _used_pow:
        return False
    _used_pow[salt] = exp
    return True
