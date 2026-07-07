"""Integration tests for user management endpoints.

Tests:
- GET/PUT /users/me — profile endpoints (auth_router)
- GET /users, GET /users/{id} — admin list endpoints (role_router)
- DELETE /users/{id} — admin soft-delete endpoint (role_router)
- Inactive user login guard
- Cross-tenant isolation
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app as _app

from src.auth.domain.entities import UserEntity, UserRole
from src.auth.infrastructure.persistence.models._user_models import User
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    _get_current_user,
)


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


# ── Fixtures for integration tests ─────────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def extra_viewer(seed_session, test_tenant_id) -> str:
    """Insert an additional VIEWER user for list tests."""
    uid = uuid4()
    seed_session.add(
        User(
            id=uid,
            name="Extra Viewer",
            dni=uid.hex[:8],
            email=f"ev-{uid.hex[:12]}@ra.test",
            password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
            role="viewer",
            tenant_id=test_tenant_id,
        )
    )
    await seed_session.commit()
    return str(uid)


@pytest_asyncio.fixture(scope="function")
async def extra_viewer_b(seed_session, test_tenant_id_b) -> str:
    """Insert a VIEWER in tenant B for cross-tenant isolation tests."""
    uid = uuid4()
    seed_session.add(
        User(
            id=uid,
            name="Extra Viewer B",
            dni=uid.hex[:8],
            email=f"evb-{uid.hex[:12]}@ra.test",
            password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
            role="viewer",
            tenant_id=test_tenant_id_b,
        )
    )
    await seed_session.commit()
    return str(uid)


class TestProfileEndpoints:
    """GET/PUT /users/me — profile endpoints."""

    async def test_get_me_returns_enriched_schema(
        self,
        test_tenant_id,
        test_admin_role_user_id,
    ) -> None:
        """GET /users/me returns 200 with enriched UserSchema."""
        from main import app

        uid = UUID(test_admin_role_user_id)
        o = _entity(uid, test_tenant_id, UserRole.ADMIN)
        app.dependency_overrides[_get_current_user] = lambda uow=None: o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.get("/auth/users/me")
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["id"] == str(uid)
            assert data["email"] is not None
            assert data["role"] == "admin"
            assert data["is_active"] is True
            assert data["tenant_id"] == str(test_tenant_id)
            assert data["name"] is not None
            assert data["dni"] is not None
        finally:
            app.dependency_overrides.clear()

    async def test_put_me_updates_name(
        self,
        test_tenant_id,
        test_admin_role_user_id,
    ) -> None:
        """PUT /users/me with name updates the user profile in the DB."""
        from main import app

        uid = UUID(test_admin_role_user_id)
        o = _entity(uid, test_tenant_id, UserRole.ADMIN, name="Old Name")
        app.dependency_overrides[_get_current_user] = lambda uow=None: o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.put("/auth/users/me", json={"name": "New Name"})
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["id"] == str(uid)
            # The use case reads the updated user from the real DB
            assert data["name"] == "New Name"
            assert data["email"] is not None
        finally:
            app.dependency_overrides.clear()

    async def test_viewer_can_access_profile(
        self,
        test_tenant_id,
        test_user_id,
    ) -> None:
        """VIEWER can access GET /users/me (no admin guard on profile)."""
        from main import app

        uid = UUID(test_user_id)
        o = _entity(uid, test_tenant_id, UserRole.VIEWER)
        app.dependency_overrides[_get_current_user] = lambda uow=None: o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.get("/auth/users/me")
            assert r.status_code == 200, r.text
        finally:
            app.dependency_overrides.clear()


class TestAdminListEndpoints:
    """GET /users, GET /users/{id} — admin list endpoints."""

    async def test_admin_can_list_users_with_pagination(
        self,
        test_tenant_id,
        test_admin_role_user_id,
        extra_viewer,
    ) -> None:
        """GET /users returns paginated list for admin."""
        from main import app

        uid = UUID(test_admin_role_user_id)
        o = _entity(uid, test_tenant_id, UserRole.ADMIN)
        app.dependency_overrides[_get_current_user] = lambda uow=None: o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.get("/auth/users?page=1&per_page=10")
            assert r.status_code == 200, r.text
            data = r.json()
            assert "items" in data
            assert "total" in data
            assert data["page"] == 1
            assert data["per_page"] == 10
            # At least the admin and the extra_viewer exist
            assert data["total"] >= 2
        finally:
            app.dependency_overrides.clear()

    async def test_viewer_cannot_list_users(
        self,
        test_tenant_id,
        test_user_id,
    ) -> None:
        """VIEWER gets 403 on GET /users."""
        from main import app

        uid = UUID(test_user_id)
        o = _entity(uid, test_tenant_id, UserRole.VIEWER)
        app.dependency_overrides[_get_current_user] = lambda uow=None: o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.get("/auth/users")
            assert r.status_code == 403, r.text
        finally:
            app.dependency_overrides.clear()

    async def test_admin_can_get_user_by_id(
        self,
        test_tenant_id,
        test_admin_role_user_id,
        extra_viewer,
    ) -> None:
        """GET /users/{id} returns a single user for admin."""
        from main import app

        uid = UUID(test_admin_role_user_id)
        o = _entity(uid, test_tenant_id, UserRole.ADMIN)
        app.dependency_overrides[_get_current_user] = lambda uow=None: o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.get(f"/auth/users/{extra_viewer}")
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["id"] == str(extra_viewer)
            assert data["email"] is not None
            assert data["role"] is not None
        finally:
            app.dependency_overrides.clear()


class TestAdminDeleteEndpoint:
    """DELETE /users/{id} — admin soft-delete endpoint."""

    async def test_admin_can_deactivate_viewer(
        self,
        test_tenant_id,
        test_admin_role_user_id,
        extra_viewer,
    ) -> None:
        """DELETE /users/{id} soft-deletes a viewer."""
        from main import app

        uid = UUID(test_admin_role_user_id)
        o = _entity(uid, test_tenant_id, UserRole.ADMIN)
        app.dependency_overrides[_get_current_user] = lambda uow=None: o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.delete(f"/auth/users/{extra_viewer}")
            assert r.status_code == 200, r.text
            data = r.json()
            assert "message" in data
        finally:
            app.dependency_overrides.clear()

    async def test_self_deactivation_returns_400(
        self,
        test_tenant_id,
        test_admin_role_user_id,
    ) -> None:
        """DELETE /users/{id} on self returns 400."""
        from main import app

        uid = UUID(test_admin_role_user_id)
        o = _entity(uid, test_tenant_id, UserRole.ADMIN)
        app.dependency_overrides[_get_current_user] = lambda uow=None: o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.delete(f"/auth/users/{uid}")
            assert r.status_code == 400, r.text
            assert "desactivarte" in r.text
        finally:
            app.dependency_overrides.clear()

    async def test_viewer_cannot_deactivate(
        self,
        test_tenant_id,
        test_user_id,
        extra_viewer,
    ) -> None:
        """VIEWER gets 403 on DELETE /users/{id}."""
        from main import app

        uid = UUID(test_user_id)
        o = _entity(uid, test_tenant_id, UserRole.VIEWER)
        app.dependency_overrides[_get_current_user] = lambda uow=None: o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.delete(f"/auth/users/{extra_viewer}")
            assert r.status_code == 403, r.text
        finally:
            app.dependency_overrides.clear()


# ── Inactive user login guard ─────────────────────────────────────────


class TestInactiveUserLogin:
    """POST /auth/login blocks inactive users."""

    @pytest_asyncio.fixture(scope="function")
    async def inactive_user_creds(self, seed_session) -> dict[str, str]:
        """Insert a user with is_active=False and return credentials."""
        from src.auth.infrastructure.persistence.models._user_models import User as UserModel

        uid = uuid4()
        user = UserModel(
            id=uid,
            name="Inactive User",
            dni=uid.hex[:8],
            email=f"inactive-{uid.hex[:12]}@ra.test",
            password="$2b$12$EcAJLTd59Ux7i7ILkWDPT.OAWaIwOTXN7ZLcxnPgFY.T0CvjYKssu",
            role="viewer",
            is_active=False,
        )
        seed_session.add(user)
        await seed_session.commit()
        return {"dni": uid.hex[:8]}

    async def test_inactive_user_returns_401(
        self,
        inactive_user_creds,
    ) -> None:
        """Login with an inactive user returns 401."""
        transport = ASGITransport(app=_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/auth/login",
                json={
                    "dni": inactive_user_creds["dni"],
                    "password": "does-not-matter",
                },
            )
        assert resp.status_code == 401, f"Inactive user login should be rejected: {resp.text}"


# ── Cross-tenant isolation tests ──────────────────────────────────────


class TestCrossTenantIsolation:
    """Admin users from tenant A cannot access users from tenant B."""

    async def test_admin_cannot_list_other_tenant_users(
        self,
        test_tenant_id,
        test_admin_role_user_id,
        extra_viewer_b,
    ) -> None:
        """GET /users from tenant A does not include tenant B users."""
        from main import app

        uid = UUID(test_admin_role_user_id)
        o = _entity(uid, test_tenant_id, UserRole.ADMIN)
        app.dependency_overrides[_get_current_user] = lambda uow=None: o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.get("/auth/users?per_page=100")
            assert r.status_code == 200, r.text
            data = r.json()
            user_ids = {item["id"] for item in data["items"]}
            assert extra_viewer_b not in user_ids, "Tenant B user should not appear in Tenant A list"
        finally:
            app.dependency_overrides.clear()

    async def test_admin_cannot_get_other_tenant_user_by_id(
        self,
        test_tenant_id,
        test_admin_role_user_id,
        extra_viewer_b,
    ) -> None:
        """GET /users/{id} from tenant A returns 404 for tenant B user."""
        from main import app

        uid = UUID(test_admin_role_user_id)
        o = _entity(uid, test_tenant_id, UserRole.ADMIN)
        app.dependency_overrides[_get_current_user] = lambda uow=None: o
        t = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=t, base_url="http://t") as c:
                r = await c.get(f"/auth/users/{extra_viewer_b}")
            assert r.status_code == 404, f"Tenant B user should not be found by Tenant A admin: {r.text}"
        finally:
            app.dependency_overrides.clear()
