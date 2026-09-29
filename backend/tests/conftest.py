"""Offline test harness.

The app reads all settings at import time (module-level ``settings =
get_settings()`` in several modules), so environment variables MUST be set
before anything from ``app`` is imported. Tests run against a throwaway
SQLite file through aiosqlite - no Postgres, no Docker.

Loop hygiene: the module-global engine lives in whichever loop the app runs
in (FastAPI TestClient's portal). All fixture-level DB work (create_all,
wipe + seed) uses a separate throwaway engine inside its own asyncio.run()
so we never reuse an aiosqlite connection across event loops.
"""

import asyncio
import os
from pathlib import Path

_TEST_DB = Path(__file__).resolve().parent / "test.db"

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["JWT_EXPIRE_MINUTES"] = "60"
os.environ["ADMIN_BOOTSTRAP_USERNAME"] = ""
os.environ["ADMIN_BOOTSTRAP_PASSWORD"] = ""
os.environ["FRONTEND_ORIGINS"] = "http://localhost"
os.environ["SUBMIT_RATE_LIMIT"] = "3/minute"  # exercised by the rate-limit test
os.environ["LOGIN_RATE_LIMIT"] = "1000/minute"  # high so auth tests never trip it
os.environ["TRUST_PROXY_HEADERS"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.database import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Admin, Answer, ExtractedName, Question, Submission  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.seed_questions import DEFAULT_QUESTIONS  # noqa: E402

TEST_ADMIN = {"username": "admin", "password": "test-pass-123"}

_ORDERED_TABLES = ["answers", "extracted_names", "submissions", "questions", "admins"]


def _run_in_fresh_loop(operation) -> None:
    """Run ``operation(conn)`` (an async callable) in its own loop + engine."""

    async def wrapper():
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.begin() as conn:
                await operation(conn)
        finally:
            await engine.dispose()

    asyncio.run(wrapper())


def _create_schema() -> None:
    async def build(conn):
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    _run_in_fresh_loop(build)


def _wipe_and_seed() -> None:
    async def reset(conn):
        for table in _ORDERED_TABLES:
            await conn.execute(text(f"DELETE FROM {table}"))

    _run_in_fresh_loop(reset)

    # Seed questions + a known admin (separate session; the wipe engine is gone).
    async def seed():
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with async_sessionmaker(engine, expire_on_commit=False)() as db:
                db.add_all(Question(**q) for q in DEFAULT_QUESTIONS)
                db.add(
                    Admin(
                        username=TEST_ADMIN["username"],
                        password_hash=hash_password(TEST_ADMIN["password"]),
                    )
                )
                await db.commit()
        finally:
            await engine.dispose()

    asyncio.run(seed())


@pytest.fixture(scope="session", autouse=True)
def _prepare_db():
    _create_schema()
    yield


@pytest.fixture()
def fresh_db():
    """Wipes every table and re-seeds the default questions + test admin."""
    _wipe_and_seed()
    yield


@pytest.fixture()
def client(fresh_db):
    # Per-IP limits are meaningless under TestClient (every request shares one
    # "testclient" address); disable unless a test explicitly re-enables.
    app.state.limiter.enabled = False
    with TestClient(app) as c:
        yield c


def login(client) -> None:
    """Logs in as the seeded admin; TestClient keeps the session cookie."""
    r = client.post(
        "/api/admin/login",
        json={"username": TEST_ADMIN["username"], "password": TEST_ADMIN["password"]},
    )
    assert r.status_code == 200, r.text


def add_submission(
    confession_text: str | None = None,
    *,
    answer_specs: list[tuple[int, str]] | None = None,
    fingerprint: str | None = None,
    created_at=None,
    ip: str | None = "10.0.0.9",
) -> None:
    """Inserts a submission directly (bypasses HTTP) for admin-view tests."""
    import uuid as _uuid
    from datetime import datetime, timezone

    async def insert():
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with async_sessionmaker(engine, expire_on_commit=False)() as db:
                sub = Submission(
                    id=_uuid.uuid4(),
                    confession_text=confession_text,
                    ip_address=ip,
                    user_agent="pytest-agent",
                    device_fingerprint=fingerprint,
                    created_at=created_at or datetime.now(timezone.utc),
                )
                for qid, option in answer_specs or []:
                    sub.answers.append(Answer(question_id=qid, selected_option=option))
                if confession_text:
                    from app.name_extraction import extract_names, normalize_name

                    for name in extract_names(confession_text):
                        sub.extracted_names.append(
                            ExtractedName(name=name, normalized_name=normalize_name(name))
                        )
                db.add(sub)
                await db.commit()
        finally:
            await engine.dispose()

    asyncio.run(insert())


def question_id_by_index(index: int, *, text_substring: str | None = None) -> int:
    """Fetches the id of the Nth seeded default question (1-based)."""

    async def fetch():
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with async_sessionmaker(engine)() as db:
                from sqlalchemy import select

                q = (
                    await db.execute(
                        select(Question).order_by(Question.order).offset(index - 1).limit(1)
                    )
                ).scalar_one()
                return q.id
        finally:
            await engine.dispose()

    return asyncio.run(fetch())


def count_rows(table: str) -> int:
    async def fetch():
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as conn:
                return (await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar_one()
        finally:
            await engine.dispose()

    return asyncio.run(fetch())