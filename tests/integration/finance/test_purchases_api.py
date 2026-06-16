"""Integration tests for the /finance/purchases API endpoint."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreatePurchaseIntegration:
    """POST /finance/purchases — create a new purchase."""

    async def test_create_purchase_returns_422_on_empty_payload(
        self,
        client: AsyncClient,
    ) -> None:
        """Missing fields return 422."""
        response = await client.post("/finance/purchases", json={})
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListPurchasesIntegration:
    """GET /finance/purchases — list purchases."""

    async def test_list_purchases_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns a list (possibly empty) of purchases."""
        response = await client.get("/finance/purchases")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
class TestGetPurchaseIntegration:
    """GET /finance/purchases/{id} — retrieve a purchase."""

    async def test_get_nonexistent_purchase_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing purchase."""
        response = await client.get(f"/finance/purchases/{uuid4()}")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDeletePurchaseIntegration:
    """DELETE /finance/purchases/{id} — delete a purchase."""

    async def test_delete_nonexistent_purchase_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing purchase."""
        response = await client.delete(f"/finance/purchases/{uuid4()}")
        assert response.status_code == 404
