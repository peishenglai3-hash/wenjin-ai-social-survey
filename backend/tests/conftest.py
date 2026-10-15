"""Shared fixtures for backend tests."""

import os
import sys
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure backend is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.models.base import Base
from app.core.database import get_db


# ── In-memory SQLite for tests ──────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest.fixture
async def test_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session backed by in-memory SQLite."""
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX async client that overrides the DB dependency."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Mock AI service for tests that don't need real API calls ────────────
class MockAIService:
    """Fake AI service that returns canned responses."""

    def __init__(self):
        self.last_usage = {}

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=4096, task=""):
        return '{"mock": "response", "task": "' + task + '"}'

    async def chat_stream(self, messages, model=None, temperature=0.7, max_tokens=4096, task=""):
        yield '{"token": "mock"}'

    async def chat_with_image(self, text, image_base64, model=None, temperature=0.7, max_tokens=4096):
        return '{"image_analysis": "mock"}'

    async def health(self):
        return True
