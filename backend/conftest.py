"""Test configuration and fixtures for all AUTOPS domain tests."""
import os
import sys
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, os.path.dirname(__file__))

from app.infra.database import Base, get_db
from app.main import create_app

TEST_DB_URL = os.environ.get(
    "TEST_DB_URL",
    "mysql+aiomysql://autops:autops_2026@127.0.0.1:3306/autops?charset=utf8mb4"
)

# Shared engine (function-scoped to avoid loop issues with aiomysql)
_test_engine = None


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def engine():
    """Create a test engine per function to avoid loop issues."""
    eng = create_async_engine(TEST_DB_URL, echo=False, pool_pre_ping=True)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session with rollback."""
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session


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
