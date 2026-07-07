"""Integration tests for role guard enforcement in the finance context.

Verifies:
  - /animal-supplies: router-level VIEWER, create/update → EDITOR, delete → ADMIN
  - /supply-types: create/update/delete/list → ADMIN
  - /purchases: router-level VIEWER, create → EDITOR, delete → ADMIN
"""

from uuid import uuid4

from httpx import AsyncClient

# ── Tests: /animal-supplies role guards ───────────────────────────────


class TestAnimalSuppliesRoleGuards:
    """Router-level VIEWER, POST/PUT → EDITOR, DELETE → ADMIN."""

    SUPPLIES_PATH = "/finance/animal-supplies"

    async def test_viewer_list_supplies(self, viewer_client: AsyncClient) -> None:
        """VIEWER can list supplies (router-level guard)."""
        response = await viewer_client.get(self.SUPPLIES_PATH)
        assert response.status_code == 200

    async def test_viewer_get_supply(self, viewer_client: AsyncClient) -> None:
        """VIEWER can get supply by id (router-level guard)."""
        response = await viewer_client.get(f"{self.SUPPLIES_PATH}/{uuid4()}")
        assert response.status_code == 404

    async def test_viewer_create_supply_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on create supply (EDITOR required)."""
        response = await viewer_client.post(self.SUPPLIES_PATH, json={})
        assert response.status_code == 403

    async def test_viewer_update_supply_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on update supply (EDITOR required)."""
        response = await viewer_client.put(f"{self.SUPPLIES_PATH}/{uuid4()}", json={})
        assert response.status_code == 403

    async def test_viewer_delete_supply_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on delete supply (ADMIN required)."""
        response = await viewer_client.delete(f"{self.SUPPLIES_PATH}/{uuid4()}")
        assert response.status_code == 403

    async def test_editor_create_supply_not_403(self, editor_client: AsyncClient) -> None:
        """EDITOR is NOT denied on create supply."""
        response = await editor_client.post(self.SUPPLIES_PATH, json={})
        assert response.status_code != 403

    async def test_editor_update_supply_not_403(self, editor_client: AsyncClient) -> None:
        """EDITOR is NOT denied on update supply."""
        response = await editor_client.put(f"{self.SUPPLIES_PATH}/{uuid4()}", json={})
        assert response.status_code != 403

    async def test_editor_delete_supply_returns_403(self, editor_client: AsyncClient) -> None:
        """EDITOR gets 403 on delete supply (ADMIN required)."""
        response = await editor_client.delete(f"{self.SUPPLIES_PATH}/{uuid4()}")
        assert response.status_code == 403


# ── Tests: /supply-types role guards ──────────────────────────────────


class TestSupplyTypesRoleGuards:
    """All CRUD operations → ADMIN only."""

    TYPES_PATH = "/finance/supply-types"

    async def test_viewer_list_types_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on list supply types (ADMIN required)."""
        response = await viewer_client.get(self.TYPES_PATH)
        assert response.status_code == 403

    async def test_viewer_create_type_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on create (ADMIN required)."""
        response = await viewer_client.post(self.TYPES_PATH, json={})
        assert response.status_code == 403

    async def test_viewer_delete_type_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on delete (ADMIN required)."""
        response = await viewer_client.delete(f"{self.TYPES_PATH}/{uuid4()}")
        assert response.status_code == 403

    async def test_editor_list_types_returns_403(self, editor_client: AsyncClient) -> None:
        """EDITOR gets 403 on list (ADMIN required)."""
        response = await editor_client.get(self.TYPES_PATH)
        assert response.status_code == 403

    async def test_admin_create_type_not_403(self, admin_role_client: AsyncClient) -> None:
        """ADMIN is NOT denied on create supply type."""
        response = await admin_role_client.post(self.TYPES_PATH, json={})
        assert response.status_code != 403

    async def test_admin_list_types_not_403(self, admin_role_client: AsyncClient) -> None:
        """ADMIN is NOT denied on list supply types."""
        response = await admin_role_client.get(self.TYPES_PATH)
        assert response.status_code != 403

    async def test_admin_delete_type_not_403(self, admin_role_client: AsyncClient) -> None:
        """ADMIN is NOT denied on delete supply type."""
        response = await admin_role_client.delete(f"{self.TYPES_PATH}/{uuid4()}")
        assert response.status_code != 403


# ── Tests: /purchases role guards ─────────────────────────────────────


class TestPurchasesRoleGuards:
    """Router-level VIEWER, POST → EDITOR, DELETE → ADMIN."""

    PURCHASES_PATH = "/finance/purchases"

    async def test_viewer_list_purchases(self, viewer_client: AsyncClient) -> None:
        """VIEWER can list purchases (router-level guard)."""
        response = await viewer_client.get(self.PURCHASES_PATH)
        assert response.status_code == 200

    async def test_viewer_get_purchase(self, viewer_client: AsyncClient) -> None:
        """VIEWER can get purchase by id (router-level guard)."""
        response = await viewer_client.get(f"{self.PURCHASES_PATH}/{uuid4()}")
        assert response.status_code == 404

    async def test_viewer_create_purchase_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on create purchase (EDITOR required)."""
        response = await viewer_client.post(self.PURCHASES_PATH, json={})
        assert response.status_code == 403

    async def test_viewer_delete_purchase_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on delete purchase (ADMIN required)."""
        response = await viewer_client.delete(f"{self.PURCHASES_PATH}/{uuid4()}")
        assert response.status_code == 403

    async def test_editor_create_purchase_not_403(self, editor_client: AsyncClient) -> None:
        """EDITOR is NOT denied on create purchase."""
        response = await editor_client.post(self.PURCHASES_PATH, json={})
        assert response.status_code != 403

    async def test_editor_delete_purchase_returns_403(self, editor_client: AsyncClient) -> None:
        """EDITOR gets 403 on delete purchase (ADMIN required)."""
        response = await editor_client.delete(f"{self.PURCHASES_PATH}/{uuid4()}")
        assert response.status_code == 403
