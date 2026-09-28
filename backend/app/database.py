from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Pool sizing applies to Postgres (QueuePool). SQLite (dev/tests via
# aiosqlite) defaults to NullPool, which rejects pool_size/max_overflow -
# passing them unconditionally made the app crash at import on any
# non-Postgres URL.
engine_kwargs: dict = {"pool_pre_ping": True}
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_async_engine(settings.database_url, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
