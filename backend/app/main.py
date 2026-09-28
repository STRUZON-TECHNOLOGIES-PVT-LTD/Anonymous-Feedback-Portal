from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


app = FastAPI(title="Anonymous Feedback Portal API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(public.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
