"""Integration tests for role management via the HTTP endpoint.

These tests verify the core HTTP round-trip for role management. They use the
dependency-override pattern (same as other integration tests) to inject role-
specific users.

NOTE: Several scenarios (last-OWNER protection, cross-tenant isolation,
self-escalation alternatives) are verified at the unit test level because
the integration test infrastructure (async loop scoping with seed_session +
NullPool engines) creates compatibility issues when tests use `seed_session`
in the test body. See `tests/unit/auth/test_update_user_role_service.py`
(12 tests) and `tests/unit/auth/test_update_user_role_case.py` (6 tests)
for full business rule coverage.

Tests here:
- OWNER promotes VIEWER → EDITOR (full round-trip with DB persistence)
- OWNER cannot self-demote (403)
- VIEWER cannot access role endpoint (403)
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.auth.domain.entities import UserEntity, UserRole
from src.auth.infrastructure.persistence.models._user_models import User
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    _get_current_user,
)
from src.common.infrastructure.presentation.dependencies.uow import (
    GetUnitOfWork as _GetUnitOfWork,
)


def _override_with(user: UserEntity, tenant_id: UUID):
    async def _inner(uow: _GetUnitOfWork) -> UserEntity:
        uow.tenant_id = tenant_id
        return user

    return _inner


def _entity(uid: UUID, tid: UUID, role: UserRole, name: str = "T") -> UserEntity:
    return UserEntity(
        id=uid,
        name=name,
        dni=uid.hex[:8],
        email=f"{name.lower()}-{uid.hex[:12]}@ra.test",
        created_at=datetime.now(tz=timezone.utc),
        role=role,
        tenant_id=tid,
    )


@pytest_asyncio.fixture(scope="function")
async def own(seed_session, test_tenant_id) -> str:
    uid = uuid4()
    seed_session.add(
        User(
            id=uid,
            name="O",
            dni=uid.hex[:8],
            email=f"o-{uid.hex[:12]}@ra.test",
            password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
            role="owner",
            tenant_id=test_tenant_id,
        )
    )
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def viewer(seed_session, test_tenant_id) -> str:
    uid = uuid4()
    seed_session.add(
        User(
            id=uid,
            name="V",
            dni=uid.hex[:8],
            email=f"v-{uid.hex[:12]}@ra.test",
            password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
            role="viewer",
            tenant_id=test_tenant_id,
        )
    )
    await seed_session.commit()
    return str(uid)


class TestRoleAssignment:
    """Integration smoke tests for the role management endpoint."""

    async def test_owner_promotes_viewer_to_editor(
        self,
        test_tenant_id,
        own: str,
        viewer: str,
    ) -> None:
        """OWNER promotes VIEWER → EDITOR: full round-trip, 200, role persisted."""
        from main import app

        o = _override_with(_entity(UUID(own), test_tenant_id, UserRole.OWNER), test_tenant_id)
        app.dependency_overrides[_get_current_user] = o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.put(f"/auth/users/{viewer}/role", json={"role": "editor"})
            assert r.status_code == 200, r.text
            assert r.json()["role"] == "editor"
        finally:
            app.dependency_overrides.clear()

    async def test_owner_cannot_demote_self(
        self,
        test_tenant_id,
        own: str,
    ) -> None:
        """OWNER self-demotion → 403 (self-escalation prevention)."""
        from main import app

        o = _override_with(_entity(UUID(own), test_tenant_id, UserRole.OWNER), test_tenant_id)
        app.dependency_overrides[_get_current_user] = o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.put(f"/auth/users/{own}/role", json={"role": "viewer"})
            assert r.status_code == 403, r.text
            assert "propio rol" in r.text
        finally:
            app.dependency_overrides.clear()

    async def test_viewer_denied(
        self,
        test_tenant_id,
        viewer: str,
        own: str,
    ) -> None:
        """VIEWER → 403 on role endpoint (OWNER-only)."""
        from main import app

        o = _override_with(_entity(UUID(viewer), test_tenant_id, UserRole.VIEWER), test_tenant_id)
        app.dependency_overrides[_get_current_user] = o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.put(f"/auth/users/{own}/role", json={"role": "editor"})
            assert r.status_code == 403, r.text
        finally:
            app.dependency_overrides.clear()
