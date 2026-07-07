"""Integration tests for role guard enforcement in the market context.

Verifies:
  - /buyers: router-level VIEWER, create/update → EDITOR, delete → ADMIN
  - /sales: router-level VIEWER, create → EDITOR, delete → ADMIN
"""

from uuid import uuid4

from httpx import AsyncClient

# ── Tests: /buyers role guards ────────────────────────────────────────


class TestBuyersRoleGuards:
    """Router-level VIEWER, POST/PUT → EDITOR, DELETE → ADMIN."""

    BUYERS_PATH = "/market/buyers"

    async def test_viewer_list_buyers(self, viewer_client: AsyncClient) -> None:
        """VIEWER can list buyers (router-level guard)."""
        response = await viewer_client.get(self.BUYERS_PATH)
        assert response.status_code == 200

    async def test_viewer_get_buyer(self, viewer_client: AsyncClient) -> None:
        """VIEWER can get buyer by id (router-level guard)."""
        response = await viewer_client.get(f"{self.BUYERS_PATH}/{uuid4()}")
        assert response.status_code == 404

    async def test_viewer_create_buyer_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on create buyer (EDITOR required)."""
        response = await viewer_client.post(self.BUYERS_PATH, json={})
        assert response.status_code == 403

    async def test_viewer_update_buyer_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on update buyer (EDITOR required)."""
        response = await viewer_client.put(f"{self.BUYERS_PATH}/{uuid4()}", json={})
        assert response.status_code == 403

    async def test_viewer_delete_buyer_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on delete buyer (ADMIN required)."""
        response = await viewer_client.delete(f"{self.BUYERS_PATH}/{uuid4()}")
        assert response.status_code == 403

    async def test_editor_create_buyer_not_403(self, editor_client: AsyncClient) -> None:
        """EDITOR is NOT denied on create buyer."""
        response = await editor_client.post(self.BUYERS_PATH, json={})
        assert response.status_code != 403

    async def test_editor_update_buyer_not_403(self, editor_client: AsyncClient) -> None:
        """EDITOR is NOT denied on update buyer."""
        response = await editor_client.put(f"{self.BUYERS_PATH}/{uuid4()}", json={})
        assert response.status_code != 403

    async def test_editor_delete_buyer_returns_403(self, editor_client: AsyncClient) -> None:
        """EDITOR gets 403 on delete buyer (ADMIN required)."""
        response = await editor_client.delete(f"{self.BUYERS_PATH}/{uuid4()}")
        assert response.status_code == 403


# ── Tests: /sales role guards ─────────────────────────────────────────


class TestSalesRoleGuards:
    """Router-level VIEWER, POST → EDITOR, DELETE → ADMIN."""

    SALES_PATH = "/market/sales"

    async def test_viewer_list_sales(self, viewer_client: AsyncClient) -> None:
        """VIEWER can list sales (router-level guard)."""
        response = await viewer_client.get(self.SALES_PATH)
        assert response.status_code == 200

    async def test_viewer_get_sale(self, viewer_client: AsyncClient) -> None:
        """VIEWER can get sale by id (router-level guard)."""
        response = await viewer_client.get(f"{self.SALES_PATH}/{uuid4()}")
        assert response.status_code == 404

    async def test_viewer_create_sale_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on create sale (EDITOR required)."""
        response = await viewer_client.post(self.SALES_PATH, json={})
        assert response.status_code == 403

    async def test_viewer_delete_sale_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on delete sale (ADMIN required)."""
        response = await viewer_client.delete(f"{self.SALES_PATH}/{uuid4()}")
        assert response.status_code == 403

    async def test_editor_create_sale_not_403(self, editor_client: AsyncClient) -> None:
        """EDITOR is NOT denied on create sale."""
        response = await editor_client.post(self.SALES_PATH, json={})
        assert response.status_code != 403

    async def test_editor_delete_sale_returns_403(self, editor_client: AsyncClient) -> None:
        """EDITOR gets 403 on delete sale (ADMIN required)."""
        response = await editor_client.delete(f"{self.SALES_PATH}/{uuid4()}")
        assert response.status_code == 403
