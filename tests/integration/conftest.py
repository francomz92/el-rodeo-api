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
os.environ.setdefault("ENABLE_RATE_LIMIT", "false")

from main import app  # noqa: E402

from src.auth.domain.entities import UserEntity  # noqa: E402
from src.auth.domain.entities._user_role import UserRole  # noqa: E402
from src.auth.infrastructure.persistence.models._tenant_model import Tenant  # noqa: E402
from src.auth.infrastructure.persistence.models._user_models import User  # noqa: E402
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (  # noqa: E402
    _get_current_user,
)
from src.cattle.domain.constants.animal import AnimalStatus  # noqa: E402
from src.cattle.infrastructure.persistence.models._animal_models import Animal, AnimalType  # noqa: E402
from src.common.application.ports.email_notifier import IEmailNotifier  # noqa: E402
from src.common.infrastructure.adapters.workers.email_workers import EmailNotifier  # noqa: E402
from src.common.infrastructure.persistence.models import Model  # noqa: E402
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork as _GetUnitOfWork  # noqa: E402
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
    """Create all tables + audit_log partitions once per session, drop after."""
    if not _db_reachable():
        pytest.skip("PostgreSQL is not reachable on localhost:5432")

    engine = create_async_engine(
        TEST_DB_URL,
        pool_size=2,
        max_overflow=2,
        echo=False,
    )
    async with engine.begin() as conn:
        # Drop first to clean up stale data from crashed runs
        await conn.run_sync(Model.metadata.drop_all)
        await conn.run_sync(Model.metadata.create_all)
        # audit_log is no longer partitioned — no manual partition creation needed
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
    await engine.dispose()


# ── Auto-use session-scoped fixture to create tables for all tests ────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def _ensure_tables(test_engine):
    """Ensure tables are created before any test runs.

    This is an independent autouse fixture so seed_session can use
    NullPool (no loop mismatch) while tables are managed separately.
    """
    pass


# ── No-op email notifier for tests (prevents Celery/kombu errors) ────


class _NoopEmailNotifier(IEmailNotifier):
    """Email notifier that swallows all sends — no Celery broker needed."""

    def send(self, to: list[str], subject: str, body: str) -> None:
        pass


# ── Function-scoped seed session ─────────────────────────────────────
# Uses the module-level NullPool engine (same as the app) to avoid
# "Future attached to a different loop" errors when pooling shares
# connections across per-test event loops.
@pytest_asyncio.fixture(scope="function")
async def seed_session() -> AsyncGenerator[AsyncSession, Any]:
    async with _nullpool_maker() as session:
        yield session


# ── Test data seeds ──────────────────────────────────────────────────
@pytest_asyncio.fixture(scope="function")
async def test_user_id(
    seed_session: AsyncSession,
    test_tenant_id: UUID,
) -> str:
    """Insert a user row with tenant and return its UUID as string."""
    uid = uuid4()
    dni = uid.hex[:8]  # login test sends this as the DNI, must match
    user = User(
        id=uid,
        name="Test User",
        dni=dni,
        email=faker.unique.email(),
        password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
        tenant_id=test_tenant_id,
    )
    seed_session.add(user)
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def test_buyer_id(
    seed_session: AsyncSession,
    test_user_id: str,
    test_tenant_id: UUID,
) -> str:
    """Insert a buyer and return its UUID."""
    uid = uuid4()
    buyer = Buyer(
        id=uid,
        user_id=UUID(test_user_id),
        tenant_id=test_tenant_id,
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


# ── Tenant fixtures ───────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def test_tenant_id(seed_session: AsyncSession) -> UUID:
    """Insert a tenant and return its UUID."""
    uid = uuid4()
    slug = f"test-tenant-{uid.hex[:8]}"
    tenant = Tenant(id=uid, name="Test Tenant", slug=slug)
    seed_session.add(tenant)
    await seed_session.commit()
    return uid


@pytest_asyncio.fixture(scope="function")
async def test_tenant_id_b(seed_session: AsyncSession) -> UUID:
    """Insert a different tenant for cross-tenant isolation tests."""
    uid = uuid4()
    slug = f"test-tenant-b-{uid.hex[:8]}"
    tenant = Tenant(id=uid, name="Test Tenant B", slug=slug)
    seed_session.add(tenant)
    await seed_session.commit()
    return uid


@pytest_asyncio.fixture(scope="function")
async def test_tenant_a_user_id(
    seed_session: AsyncSession,
    test_tenant_id: UUID,
) -> str:
    """Insert a user belonging to Tenant A and return its UUID.

    Creates a user with tenant_id set to test_tenant_id.
    """
    uid = uuid4()
    dni = uid.hex[:8]
    user = User(
        id=uid,
        name="Tenant A User",
        dni=dni,
        email=faker.unique.email(),
        password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
        tenant_id=test_tenant_id,
    )
    seed_session.add(user)
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def test_tenant_b_user_id(
    seed_session: AsyncSession,
    test_tenant_id_b: UUID,
) -> str:
    """Insert a user belonging to Tenant B and return its UUID."""
    uid = uuid4()
    dni = uid.hex[:8]
    user = User(
        id=uid,
        name="Tenant B User",
        dni=dni,
        email=faker.unique.email(),
        password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
        tenant_id=test_tenant_id_b,
    )
    seed_session.add(user)
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def test_viewer_user_id(
    seed_session: AsyncSession,
    test_tenant_id: UUID,
) -> str:
    """Insert a VIEWER user into the DB."""
    uid = uuid4()
    user = User(
        id=uid,
        name="Viewer User",
        dni=uid.hex[:8],
        email=faker.unique.email(),
        password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
        role="viewer",
        tenant_id=test_tenant_id,
    )
    seed_session.add(user)
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def test_editor_user_id(
    seed_session: AsyncSession,
    test_tenant_id: UUID,
) -> str:
    """Insert an EDITOR user into the DB."""
    uid = uuid4()
    user = User(
        id=uid,
        name="Editor User",
        dni=uid.hex[:8],
        email=faker.unique.email(),
        password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
        role="editor",
        tenant_id=test_tenant_id,
    )
    seed_session.add(user)
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def test_admin_role_user_id(
    seed_session: AsyncSession,
    test_tenant_id: UUID,
) -> str:
    """Insert an ADMIN-by-role user into the DB."""
    uid = uuid4()
    user = User(
        id=uid,
        name="Admin Role User",
        dni=uid.hex[:8],
        email=faker.unique.email(),
        password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
        role="admin",
        tenant_id=test_tenant_id,
    )
    seed_session.add(user)
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def test_admin_user_id(
    seed_session: AsyncSession,
    test_tenant_id: UUID,
) -> str:
    """Insert a SUPER_ADMIN user belonging to Tenant A and return its UUID."""
    uid = uuid4()
    dni = uid.hex[:8]
    user = User(
        id=uid,
        name="Super Admin User",
        dni=dni,
        email=faker.unique.email(),
        password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
        role="super_admin",
        tenant_id=test_tenant_id,
    )
    seed_session.add(user)
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def test_animal_id(
    seed_session: AsyncSession,
    test_user_id: str,
    test_animal_type_id: str,
    test_tenant_id: UUID,
) -> str:
    """Insert an animal and return its UUID."""
    uid = uuid4()
    animal = Animal(
        id=uid,
        user_id=UUID(test_user_id),
        tenant_id=test_tenant_id,
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
async def client(
    test_user_id: str,
    test_tenant_id: UUID,
) -> AsyncGenerator[AsyncClient, Any]:
    """Provide an HTTPX AsyncClient against the FastAPI app.

    Auth is bypassed: the user from `test_user_id` is injected automatically.
    The app manages its own DB connections (via env DB_URL).
    The tenant_id from test_tenant_id is set on the UoW so TenantAwareRepository
    instances work correctly.
    """
    uid = UUID(test_user_id)
    tid = test_tenant_id
    user = UserEntity(
        id=uid,
        name="Test User",
        dni=uid.hex[:8],
        email=f"test-{uid.hex[:8]}@example.com",
        created_at=datetime.now(tz=timezone.utc),
        role=UserRole.ADMIN,
        tenant_id=tid,
    )

    async def _override_current_user(
        uow: _GetUnitOfWork,
    ) -> UserEntity:
        uow.tenant_id = tid
        return user

    app.dependency_overrides[_get_current_user] = _override_current_user
    app.dependency_overrides[EmailNotifier] = lambda: _NoopEmailNotifier()

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def tenant_client(
    test_tenant_a_user_id: str,
    test_tenant_id: UUID,
) -> AsyncGenerator[AsyncClient, Any]:
    """Provide an HTTPX AsyncClient with a Tenant A user (non-admin).

    Auth is bypassed via dependency_overrides. The override function
    also sets uow.tenant_id so TenantAwareRepository instances work.
    """
    uid = UUID(test_tenant_a_user_id)
    user = UserEntity(
        id=uid,
        name="Tenant A User",
        dni=uid.hex[:8],
        email=f"tenant-a-{uid.hex[:8]}@example.com",
        created_at=datetime.now(tz=timezone.utc),
        role=UserRole.ADMIN,
        tenant_id=test_tenant_id,
    )
    tid = test_tenant_id

    async def _override_current_user(
        uow: _GetUnitOfWork,
    ) -> UserEntity:
        uow.tenant_id = tid
        return user

    app.dependency_overrides[_get_current_user] = _override_current_user

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def tenant_b_client(
    test_tenant_b_user_id: str,
    test_tenant_id_b: UUID,
) -> AsyncGenerator[AsyncClient, Any]:
    """Provide an HTTPX AsyncClient with a Tenant B user (non-admin).

    Auth is bypassed via dependency_overrides. The override function
    also sets uow.tenant_id so TenantAwareRepository instances work.
    """
    uid = UUID(test_tenant_b_user_id)
    user = UserEntity(
        id=uid,
        name="Tenant B User",
        dni=uid.hex[:8],
        email=f"tenant-b-{uid.hex[:8]}@example.com",
        created_at=datetime.now(tz=timezone.utc),
        role=UserRole.ADMIN,
        tenant_id=test_tenant_id_b,
    )
    tid = test_tenant_id_b

    async def _override_current_user(
        uow: _GetUnitOfWork,
    ) -> UserEntity:
        uow.tenant_id = tid
        return user

    app.dependency_overrides[_get_current_user] = _override_current_user

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def super_admin_client(
    test_admin_user_id: str,
    test_tenant_id: UUID,
) -> AsyncGenerator[AsyncClient, Any]:
    """Provide an HTTPX AsyncClient with a SUPER_ADMIN user from Tenant A.

    Auth is bypassed via dependency_overrides. The override function
    sets uow.tenant_id and also enables bypass_filter for cross-tenant
    super-admin access.
    """
    uid = UUID(test_admin_user_id)
    user = UserEntity(
        id=uid,
        name="Super Admin User",
        dni=uid.hex[:8],
        email=f"super-admin-{uid.hex[:8]}@example.com",
        created_at=datetime.now(tz=timezone.utc),
        role=UserRole.SUPER_ADMIN,
        tenant_id=test_tenant_id,
    )
    tid = test_tenant_id

    async def _override_super_admin_current_user(
        uow: _GetUnitOfWork,
    ) -> UserEntity:
        uow.tenant_id = tid
        uow.bypass_filter = True
        return user

    app.dependency_overrides[_get_current_user] = _override_super_admin_current_user

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def editor_client(
    test_editor_user_id: str,
    test_tenant_id: UUID,
) -> AsyncGenerator[AsyncClient, Any]:
    """HTTPX client authenticated with an EDITOR-role user."""
    uid = UUID(test_editor_user_id)
    user = UserEntity(
        id=uid,
        name="Editor User",
        dni=uid.hex[:8],
        email=f"editor-{uid.hex[:8]}@example.com",
        created_at=datetime.now(tz=timezone.utc),
        role=UserRole.EDITOR,
        tenant_id=test_tenant_id,
    )
    tid = test_tenant_id

    async def _override(uow: _GetUnitOfWork) -> UserEntity:
        uow.tenant_id = tid
        return user

    app.dependency_overrides[_get_current_user] = _override
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def admin_role_client(
    test_admin_role_user_id: str,
    test_tenant_id: UUID,
) -> AsyncGenerator[AsyncClient, Any]:
    """HTTPX client authenticated with an ADMIN-role user."""
    uid = UUID(test_admin_role_user_id)
    user = UserEntity(
        id=uid,
        name="Admin Role User",
        dni=uid.hex[:8],
        email=f"admin-role-{uid.hex[:8]}@example.com",
        created_at=datetime.now(tz=timezone.utc),
        role=UserRole.ADMIN,
        tenant_id=test_tenant_id,
    )
    tid = test_tenant_id

    async def _override(uow: _GetUnitOfWork) -> UserEntity:
        uow.tenant_id = tid
        return user

    app.dependency_overrides[_get_current_user] = _override
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def viewer_client(
    test_viewer_user_id: str,
    test_tenant_id: UUID,
) -> AsyncGenerator[AsyncClient, Any]:
    """HTTPX client authenticated with a VIEWER-role user (for role-guard tests)."""
    uid = UUID(test_viewer_user_id)
    user = UserEntity(
        id=uid,
        name="Viewer User",
        dni=uid.hex[:8],
        email=f"viewer-{uid.hex[:8]}@example.com",
        created_at=datetime.now(tz=timezone.utc),
        role=UserRole.VIEWER,
        tenant_id=test_tenant_id,
    )
    tid = test_tenant_id

    async def _override(uow: _GetUnitOfWork) -> UserEntity:
        uow.tenant_id = tid
        return user

    app.dependency_overrides[_get_current_user] = _override
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
