import os
import tempfile
# Must be set BEFORE any app imports
os.environ.setdefault("ANALIZAVET_ENV", "default")
os.environ.setdefault("ANALIZAVET_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ANALIZAVET_IMAGES_DIR", tempfile.mkdtemp())

import dramatiq
from dramatiq.brokers.stub import StubBroker

# CRITICAL: Set stub broker BEFORE any app imports that register dramatiq actors.
# This ensures actors are registered with the stub broker, not the default Redis broker.
_test_stub_broker = StubBroker()
dramatiq.set_broker(_test_stub_broker)

import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_session


# ── Dramatiq Stub Broker fixture (exposes the broker for tests) ────────────────

@pytest.fixture(scope="session", autouse=True)
def stub_broker():
    """Expose the pre-configured stub broker for test use."""
    yield _test_stub_broker


# ── Shared in-memory engine (session scope) ────────────────────────────────────

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    return _engine


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    await engine.dispose()
    global _engine
    _engine = None


async def _override_get_session():
    maker = sessionmaker(_get_engine(), class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest.fixture
async def client():
    app.dependency_overrides[get_session] = _override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
