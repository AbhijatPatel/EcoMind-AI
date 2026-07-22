"""
Database engine and session management.

Uses SQLAlchemy's async engine (asyncpg driver) so that DB I/O never blocks
FastAPI's event loop. Pool size/overflow are explicit rather than left to
library defaults, since silent default pooling is a common source of
"works locally, exhausts connections in production" bugs.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# SQLite (used in tests) uses StaticPool and rejects pool_size/max_overflow
# outright. Postgres (asyncpg) uses QueuePool and needs them set explicitly
# rather than left at library defaults.
_engine_kwargs: dict = {"echo": settings.debug, "pool_pre_ping": True}
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs["pool_size"] = settings.db_pool_size
    _engine_kwargs["max_overflow"] = settings.db_max_overflow

engine = create_async_engine(settings.database_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models (defined in Phase 5)."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a request-scoped async session and
    guarantees it is closed afterwards, even if the request raises.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
