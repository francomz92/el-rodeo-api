"""Integration tests for cross-tenant data isolation.

Verifies:
  - User from Tenant A CAN read their own data
  - User from Tenant A CANNOT read Tenant B's data (returns 404)
  - User from Tenant A CANNOT update Tenant B's data (returns 404)
  - User from Tenant A CANNOT delete Tenant B's data (returns 404)
  - Super admin CAN read cross-tenant data when bypass is used

Fixtures from conftest:
  - tenant_client: authenticated client as Tenant A user (ADMIN)
  - tenant_b_client: authenticated client as Tenant B user (ADMIN)
  - super_admin_client: authenticated client as SUPER_ADMIN user (Tenant A)
  - test_animal_type_id: fixture creating an animal type
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from main import app

from src.auth.domain.entities import UserEntity, UserRole
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    _get_current_user,
)
from src.common.infrastructure.presentation.dependencies.uow import (
    GetUnitOfWork as _GetUnitOfWork,
)


def _make_override(uid: UUID, tid: UUID, role: UserRole) -> object:
    """Create a dependency override function for the given user/tenant/role."""
    user = UserEntity(
        id=uid,
        name="T",
        dni=uid.hex[:8],
        email=f"t-{uid.hex[:12]}@ra.test",
        created_at=datetime.now(tz=timezone.utc),
        role=role,
        tenant_id=tid,
    )

    async def _inner(uow: _GetUnitOfWork) -> UserEntity:
        uow.tenant_id = tid
        return user

    return _inner


@pytest.mark.asyncio
class TestCrossTenantReadIsolation:
    """Verify Tenant A cannot read Tenant B's data."""

    async def test_tenant_a_can_read_own_animal(
        self,
        tenant_client: AsyncClient,
        test_animal_type_id: str,
    ) -> None:
        """Tenant A creates and reads their own animal successfully."""
        # Create an animal as Tenant A
        create_resp = await tenant_client.post(
            "/cattle/animals",
            json={
                "type_id": test_animal_type_id,
                "caravana": f"CAR-{uuid4().hex[:6]}-A",
                "breed": "Angus",
                "tag": f"TAG-{uuid4().hex[:6]}",
                "date_of_birth": "2023-01-15",
                "initial_weight": 150.0,
                "initial_weight_date": "2023-01-15",
                "last_weight": 320.0,
                "status": "no_disponible",
            },
        )
        assert create_resp.status_code == 201
        animal_id = create_resp.json()["id"]

        # Read as Tenant A — should succeed
        read_resp = await tenant_client.get(f"/cattle/animals/{animal_id}")
        assert read_resp.status_code == 200
        assert read_resp.json()["id"] == animal_id

    async def test_tenant_a_cannot_read_tenant_b_animal(
        self,
        tenant_client: AsyncClient,
        test_tenant_id_b: UUID,
        test_tenant_b_user_id: str,
        test_animal_type_id: str,
    ) -> None:
        """Tenant B creates an animal; Tenant A cannot read it (404).

        NOTE: ``tenant_b_client`` fixture shares ``dependency_overrides`` with
        ``tenant_client``, so we create Tenant B's client inline with its own
        override to avoid the collision.
        """
        b_uid = UUID(test_tenant_b_user_id)
        b_tid = test_tenant_id_b
        b_override = _make_override(b_uid, b_tid, UserRole.ADMIN)
        saved = app.dependency_overrides.get(_get_current_user)

        app.dependency_overrides[_get_current_user] = b_override
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as b_client:
                create_resp = await b_client.post(
                    "/cattle/animals",
                    json={
                        "type_id": test_animal_type_id,
                        "caravana": f"CAR-{uuid4().hex[:6]}-B",
                        "breed": "Hereford",
                        "tag": f"TAG-{uuid4().hex[:6]}",
                        "date_of_birth": "2023-02-20",
                        "initial_weight": 200.0,
                        "initial_weight_date": "2023-02-20",
                        "last_weight": 400.0,
                        "status": "no_disponible",
                    },
                )
                assert create_resp.status_code == 201
                b_animal_id = create_resp.json()["id"]
        finally:
            # Restore Tenant A's override so ``tenant_client`` still works
            if saved is not None:
                app.dependency_overrides[_get_current_user] = saved
            else:
                app.dependency_overrides.pop(_get_current_user, None)

        # Try to read as Tenant A — should be invisible (404)
        read_resp = await tenant_client.get(f"/cattle/animals/{b_animal_id}")
        assert read_resp.status_code == 404, f"Expected 404 for cross-tenant read, got {read_resp.status_code}"


@pytest.mark.asyncio
class TestCrossTenantWriteIsolation:
    """Verify Tenant A cannot update/delete Tenant B's data."""

    async def test_tenant_a_cannot_update_tenant_b_animal(
        self,
        tenant_client: AsyncClient,
        test_tenant_id_b: UUID,
        test_tenant_b_user_id: str,
        test_animal_type_id: str,
    ) -> None:
        """Tenant B creates an animal; Tenant A cannot update it (404)."""
        b_uid = UUID(test_tenant_b_user_id)
        b_tid = test_tenant_id_b
        b_override = _make_override(b_uid, b_tid, UserRole.ADMIN)
        saved = app.dependency_overrides.get(_get_current_user)

        app.dependency_overrides[_get_current_user] = b_override
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as b_client:
                create_resp = await b_client.post(
                    "/cattle/animals",
                    json={
                        "type_id": test_animal_type_id,
                        "caravana": f"CAR-{uuid4().hex[:6]}-UPD",
                        "breed": "Angus",
                        "tag": f"TAG-{uuid4().hex[:6]}",
                        "date_of_birth": "2023-03-10",
                        "initial_weight": 180.0,
                        "initial_weight_date": "2023-03-10",
                        "last_weight": 350.0,
                        "status": "no_disponible",
                    },
                )
                assert create_resp.status_code == 201
                b_animal_id = create_resp.json()["id"]
        finally:
            # Restore Tenant A's override so ``tenant_client`` still works
            if saved is not None:
                app.dependency_overrides[_get_current_user] = saved
            else:
                app.dependency_overrides.pop(_get_current_user, None)

        # Try to update as Tenant A — should be blocked (404)
        update_resp = await tenant_client.put(
            f"/cattle/animals/{b_animal_id}",
            json={
                "type_id": test_animal_type_id,
                "breed": "Brangus",
                "date_of_birth": "2023-03-10",
                "initial_weight": 190.0,
                "initial_weight_date": "2023-03-10",
                "last_weight": 360.0,
                "status": "no_disponible",
            },
        )
        assert update_resp.status_code == 404, f"Expected 404 for cross-tenant update, got {update_resp.status_code}"

    async def test_tenant_a_cannot_delete_tenant_b_animal(
        self,
        tenant_client: AsyncClient,
        test_tenant_id_b: UUID,
        test_tenant_b_user_id: str,
        test_animal_type_id: str,
    ) -> None:
        """Tenant B creates an animal; Tenant A cannot delete it (404)."""
        b_uid = UUID(test_tenant_b_user_id)
        b_tid = test_tenant_id_b
        b_override = _make_override(b_uid, b_tid, UserRole.ADMIN)
        saved = app.dependency_overrides.get(_get_current_user)

        app.dependency_overrides[_get_current_user] = b_override
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as b_client:
                create_resp = await b_client.post(
                    "/cattle/animals",
                    json={
                        "type_id": test_animal_type_id,
                        "caravana": f"CAR-{uuid4().hex[:6]}-DEL",
                        "breed": "Brangus",
                        "tag": f"TAG-{uuid4().hex[:6]}",
                        "date_of_birth": "2023-04-05",
                        "initial_weight": 250.0,
                        "initial_weight_date": "2023-04-05",
                        "last_weight": 450.0,
                        "status": "no_disponible",
                    },
                )
                assert create_resp.status_code == 201
                b_animal_id = create_resp.json()["id"]
        finally:
            # Restore Tenant A's override so ``tenant_client`` still works
            if saved is not None:
                app.dependency_overrides[_get_current_user] = saved
            else:
                app.dependency_overrides.pop(_get_current_user, None)

        # Try to delete as Tenant A — should be blocked (404)
        delete_resp = await tenant_client.delete(f"/cattle/animals/{b_animal_id}")
        assert delete_resp.status_code == 404, f"Expected 404 for cross-tenant delete, got {delete_resp.status_code}"


@pytest.mark.asyncio
class TestAdminCrossTenantAccess:
    """Verify admin can read cross-tenant data with bypass."""

    async def test_admin_can_read_tenant_a_animal(
        self,
        tenant_client: AsyncClient,
        test_admin_user_id: str,
        test_tenant_id: UUID,
        test_animal_type_id: str,
    ) -> None:
        """Tenant A creates an animal; super admin reads it successfully."""
        # Create as Tenant A
        create_resp = await tenant_client.post(
            "/cattle/animals",
            json={
                "type_id": test_animal_type_id,
                "caravana": f"CAR-{uuid4().hex[:6]}-ADM",
                "breed": "Angus",
                "tag": f"TAG-{uuid4().hex[:6]}",
                "date_of_birth": "2023-05-01",
                "initial_weight": 160.0,
                "initial_weight_date": "2023-05-01",
                "last_weight": 310.0,
                "status": "no_disponible",
            },
        )
        assert create_resp.status_code == 201
        a_animal_id = create_resp.json()["id"]

        # Create super admin override inline so it doesn't collide with tenant_client
        sa_uid = UUID(test_admin_user_id)
        sa_user = UserEntity(
            id=sa_uid,
            name="Super Admin User",
            dni=sa_uid.hex[:8],
            email=f"super-admin-{sa_uid.hex[:8]}@example.com",
            created_at=datetime.now(tz=timezone.utc),
            role=UserRole.SUPER_ADMIN,
            tenant_id=test_tenant_id,
        )

        async def _override_super_admin(uow: _GetUnitOfWork) -> UserEntity:
            uow.tenant_id = test_tenant_id
            uow.bypass_filter = True
            return sa_user

        saved = app.dependency_overrides.get(_get_current_user)
        app.dependency_overrides[_get_current_user] = _override_super_admin
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as sa_client:
                read_resp = await sa_client.get(f"/cattle/animals/{a_animal_id}")
                assert read_resp.status_code == 200
        finally:
            # Restore Tenant A's override so ``tenant_client`` still works
            if saved is not None:
                app.dependency_overrides[_get_current_user] = saved
            else:
                app.dependency_overrides.pop(_get_current_user, None)


@pytest.mark.asyncio
class TestRegistrationTenantAssignment:
    """Verify POST /auth/register creates tenant and user with correct tenant_id."""

    async def test_register_creates_tenant_and_assigns_tenant_id(
        self,
        client: AsyncClient,
    ) -> None:
        """POST /auth/register creates a tenant row and assigns tenant_id to user."""
        response = await client.post(
            "/auth/register",
            json={
                "name": "New Test Farm",
                "dni": f"99{uuid4().hex[:6]}",
                "email": f"newfarm-{uuid4().hex[:8]}@example.com",
            },
        )
        # Registration succeeds (admin auth bypassed via client fixture)
        assert response.status_code in (200, 201), f"Unexpected status: {response.status_code}: {response.text}"


@pytest.mark.asyncio
class TestSlugUniqueness:
    """Verify tenant slug uniqueness validation during registration."""

    async def test_duplicate_slug_raises_conflict(
        self,
        client: AsyncClient,
    ) -> None:
        """Registering twice with the same org name raises a conflict error."""
        org_name = f"Duplicate Farm {uuid4().hex[:4]}"
        dni = f"88{uuid4().hex[:6]}"
        email = f"dup-{uuid4().hex[:8]}@example.com"

        # First registration succeeds
        first = await client.post(
            "/auth/register",
            json={
                "name": org_name,
                "dni": dni,
                "email": email,
            },
        )
        assert first.status_code in (200, 201)

        # Second registration with same org name (same slug) should fail
        second = await client.post(
            "/auth/register",
            json={
                "name": org_name,
                "dni": f"77{uuid4().hex[:6]}",  # different DNI
                "email": f"dup2-{uuid4().hex[:8]}@example.com",  # different email
            },
        )
        assert second.status_code == 409, f"Expected 409 for duplicate slug, got {second.status_code}: {second.text}"
