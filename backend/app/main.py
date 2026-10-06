from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models import Admin, Question
from app.rate_limit import limiter
from app.routers import admin, public
from app.security import hash_password
from app.seed_questions import DEFAULT_QUESTIONS

settings = get_settings()


async def _seed_questions_if_empty() -> None:
    async with AsyncSessionLocal() as db:
        count = (await db.execute(select(Question))).first()
        if count is None:
            db.add_all(Question(**q) for q in DEFAULT_QUESTIONS)
            await db.commit()


async def _bootstrap_admin_if_needed() -> None:
    if not settings.admin_bootstrap_username or not settings.admin_bootstrap_password:
        return

    async with AsyncSessionLocal() as db:
        existing = (
            await db.execute(select(Admin).where(Admin.username == settings.admin_bootstrap_username))
        ).scalar_one_or_none()
        if existing:
            return

        db.add(
            Admin(
                username=settings.admin_bootstrap_username,
                password_hash=hash_password(settings.admin_bootstrap_password),
            )
        )
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _seed_questions_if_empty()
    await _bootstrap_admin_if_needed()
    yield


app = FastAPI(
    title="Anonymous Feedback Portal API",
    lifespan=lifespan,
    # No public API schema/UI in production.
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)


@app.middleware("http")
async def security_middleware(request, call_next):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > settings.max_body_bytes:
        return JSONResponse({"detail": "Request body too large"}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    if request.url.path.startswith("/api/admin"):
        response.headers["Cache-Control"] = "no-store"
    return response


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(public.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
