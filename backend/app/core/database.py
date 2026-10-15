"""Async SQLAlchemy engine and session factory.

Supports both SQLite (dev) and PostgreSQL (prod) via the DATABASE_URL setting.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _create_engine():
    """Create async engine with appropriate settings for the database backend."""
    url = settings.database_url
    connect_args: dict = {}

    if "postgresql" in url or "asyncpg" in url:
        # PostgreSQL with asyncpg — connection pooling
        return create_async_engine(
            url,
            echo=False,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_recycle=settings.db_pool_recycle,
            pool_pre_ping=True,  # Verify connections before use
        )
    else:
        # SQLite with aiosqlite — single connection (no pool needed)
        connect_args = {"check_same_thread": False}
        return create_async_engine(
            url,
            echo=False,
            connect_args=connect_args,
        )


engine = _create_engine()
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """FastAPI dependency — yields an async database session."""
    async with async_session_factory() as session:
        yield session
