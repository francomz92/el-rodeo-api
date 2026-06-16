"""Integration test fixtures — test database, test client, and auth stubs.

Database strategy:
  - Set `DB_URL` env var to `el_rodeo_test` BEFORE the app is imported.
  - A session-scoped test engine creates/drops tables once.
  - The app's DB engine is monkey-patched to NullPool so each test gets
    its own asyncpg connections (no cross-loop pool reuse).
  - Auth is bypassed via dependency_overrides on `_get_current_user`.
  - Seeds use SQLAlchemy ORM models with Faker for realistic, reproducible data.
"""

import os
import socket
from collections.abc import AsyncGenerator
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# ── Force test databases BEFORE importing any app modules ─────────────
os.environ.setdefault(
    "DB_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/el_rodeo_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6380/9")

from main import app  # noqa: E402

from src.auth.domain.entities import UserEntity  # noqa: E402
from src.auth.infrastructure.persistence.models._user_models import User  # noqa: E402
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (  # noqa: E402
    _get_current_admin_user,
    _get_current_user,
)
from src.cattle.domain.constants.animal import AnimalStatus  # noqa: E402
from src.cattle.infrastructure.persistence.models._animal_models import Animal, AnimalType  # noqa: E402
from src.common.infrastructure.persistence.models import Model  # noqa: E402
from src.market.infrastructure.persistence.models._buyers import Buyer  # noqa: E402

TEST_DB_URL = os.environ["DB_URL"]

# ── Faker — reproducible seed, Argentine Spanish locale ───────────────
faker = Faker("es_AR")
Faker.seed(42)

# ── Patch the app's DB engine to NullPool ────────────────────────────
# Without this, asyncpg connections from the pool get reused across
# different event loops (pytest-asyncio per-test loops) and crash with
# "Future attached to a different loop".
from src.common.infrastructure.persistence.connections import db as _app_db  # noqa: E402
from src.common.infrastructure.presentation.dependencies import db as _db_dep  # noqa: E402

_nullpool_engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
_nullpool_maker = async_sessionmaker(
    bind=_nullpool_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
_app_db.engine = _nullpool_engine
_app_db.AsyncSessionMaker = _nullpool_maker
_db_dep.AsyncSessionMaker = _nullpool_maker


def _db_reachable() -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect(("localhost", 5432))
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


# ── Session-scoped engine — table management ─────────────────────────
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create all tables once per session, drop after."""
    if not _db_reachable():
        pytest.skip("PostgreSQL is not reachable on localhost:5432")

    engine = create_async_engine(
        TEST_DB_URL,
        pool_size=2,
        max_overflow=2,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
    await engine.dispose()


# ── Session-scoped seed session maker ────────────────────────────────
@pytest_asyncio.fixture(scope="session")
async def seed_maker(test_engine):
    """Reusable session factory for seeding test data."""
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )


# ── Function-scoped seed session ─────────────────────────────────────
# NOT shared with the app. Use only to INSERT rows before tests,
# then close it so the app can use its own connections.
@pytest_asyncio.fixture(scope="function")
async def seed_session(seed_maker) -> AsyncGenerator[AsyncSession, Any]:
    async with seed_maker() as session:
        yield session


# ── Test data seeds ──────────────────────────────────────────────────
@pytest_asyncio.fixture(scope="function")
async def test_user_id(seed_session: AsyncSession) -> str:
    """Insert a user row and return its UUID as string."""
    uid = uuid4()
    dni = uid.hex[:8]  # login test sends this as the DNI, must match
    user = User(
        id=uid,
        name="Test User",
        dni=dni,
        email=faker.unique.email(),
        password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
        is_admin=False,
    )
    seed_session.add(user)
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def test_buyer_id(seed_session: AsyncSession, test_user_id: str) -> str:
    """Insert a buyer and return its UUID."""
    uid = uuid4()
    buyer = Buyer(
        id=uid,
        user_id=UUID(test_user_id),
        name=faker.name(),
        description="Comprador de prueba",
        contact_number=faker.bothify(text="##########"),
        contact_address=faker.street_address(),
    )
    seed_session.add(buyer)
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def test_animal_type_id(seed_session: AsyncSession) -> str:
    """Insert an animal type and return its UUID."""
    uid = uuid4()
    animal_type = AnimalType(
        id=uid,
        name=faker.unique.bothify(text="Novillo-???##"),
    )
    seed_session.add(animal_type)
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def test_animal_id(
    seed_session: AsyncSession,
    test_user_id: str,
    test_animal_type_id: str,
) -> str:
    """Insert an animal and return its UUID."""
    uid = uuid4()
    animal = Animal(
        id=uid,
        user_id=UUID(test_user_id),
        type_id=UUID(test_animal_type_id),
        caravana=faker.unique.bothify(text="CAR-??????"),
        tag=faker.bothify(text="TAG-??????"),
        date_of_birth=date(2023, 1, 15),
        initial_weight=150.0,
        initial_weight_date=date(2023, 1, 15),
        last_weight=320.0,
        breed="Angus",
        status=AnimalStatus.READY,
    )
    seed_session.add(animal)
    await seed_session.commit()
    return str(uid)


# ── Redis reachability ────────────────────────────────────────────────
def _redis_reachable() -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect(("localhost", 6379))
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


# ── Authenticated test client ────────────────────────────────────────
@pytest_asyncio.fixture(scope="function")
async def client(test_user_id: str) -> AsyncGenerator[AsyncClient, Any]:
    """Provide an HTTPX AsyncClient against the FastAPI app.

    Auth is bypassed: the user from `test_user_id` is injected automatically.
    The app manages its own DB connections (via env DB_URL).
    """
    uid = UUID(test_user_id)
    user = UserEntity(
        id=uid,
        name="Test User",
        dni=uid.hex[:8],
        email=f"test-{uid.hex[:8]}@example.com",
        created_at=datetime.now(tz=timezone.utc),
        is_admin=False,
    )

    app.dependency_overrides[_get_current_user] = lambda: user
    app.dependency_overrides[_get_current_admin_user] = lambda: user

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
