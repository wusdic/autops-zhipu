"""Test configuration and fixtures."""
import asyncio
import sys
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.infra.database import get_db
from app.main import create_app

# Use a test database (same server, different db for isolation)
TEST_DB_URL = os.environ.get(
    "TEST_DB_URL",
    "mysql+aiomysql://autops:autops_2026@127.0.0.1:3306/autops?charset=utf8mb4"
)

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create test engine."""
    eng = create_async_engine(TEST_DB_URL, echo=False, pool_pre_ping=True)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test database session."""
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP test client with DB session override."""
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
