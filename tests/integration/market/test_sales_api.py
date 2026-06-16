"""Integration tests for the /market/sales API endpoint.

Each test runs against a real test database with full stack:
  router → use case → domain service → repository → SQLAlchemy → asyncpg

Fixtures provide:
  - An authenticated test user
  - Existing buyer and animal records for FK constraints
"""

from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreateSaleIntegration:
    """POST /market/sales — create a new sale."""

    async def test_create_sale_returns_201(
        self,
        client: AsyncClient,
        test_buyer_id: str,
        test_animal_id: str,
    ) -> None:
        """A valid sale creation returns 201 with the created sale data."""
        payload = {
            "animal_id": test_animal_id,
            "buyer_id": test_buyer_id,
            "sale_date": "2024-06-15",
            "price": 1500.00,
            "price_per_kg": 12.50,
            "weight": 120.0,
            "description": "Venta de novillo",
        }

        response = await client.post("/market/sales", json=payload)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        body = response.json()
        assert body["id"] is not None
        assert body["price"] == 1500.00
        assert body["weight"] == 120.0
        assert isinstance(UUID(body["id"]), UUID)

    async def test_create_sale_returns_422_on_empty_payload(
        self,
        client: AsyncClient,
    ) -> None:
        """Missing required fields return 422 validation error."""
        response = await client.post("/market/sales", json={})

        assert response.status_code == 422

    async def test_create_sale_returns_422_on_invalid_types(
        self,
        client: AsyncClient,
        test_buyer_id: str,
        test_animal_id: str,
    ) -> None:
        """Wrong data types (string for float) return 422."""
        payload = {
            "animal_id": test_animal_id,
            "buyer_id": test_buyer_id,
            "sale_date": "not-a-date",
            "price": "not-a-number",
            "price_per_kg": "not-a-number",
            "weight": "not-a-number",
        }

        response = await client.post("/market/sales", json=payload)

        assert response.status_code == 422


@pytest.mark.asyncio
class TestGetSaleIntegration:
    """GET /market/sales/{id} — retrieve a single sale."""

    async def test_get_sale_returns_200(
        self,
        client: AsyncClient,
        test_buyer_id: str,
        test_animal_id: str,
    ) -> None:
        """Returns the sale data when the sale exists."""
        # Create a sale first
        create_resp = await client.post(
            "/market/sales",
            json={
                "animal_id": test_animal_id,
                "buyer_id": test_buyer_id,
                "sale_date": "2024-06-15",
                "price": 1500.00,
                "price_per_kg": 12.50,
                "weight": 120.0,
                "description": "Venta de novillo",
            },
        )
        sale_id = create_resp.json()["id"]

        # Retrieve it
        response = await client.get(f"/market/sales/{sale_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == sale_id
        assert body["price"] == 1500.00

    async def test_get_nonexistent_sale_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing sale."""
        from uuid import uuid4

        response = await client.get(f"/market/sales/{uuid4()}")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestListSalesIntegration:
    """GET /market/sales — list sales for the authenticated user."""

    async def test_list_sales_is_empty_initially(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns an empty list when there are no sales for this user."""
        response = await client.get("/market/sales")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_sales_returns_created_sales(
        self,
        client: AsyncClient,
        test_buyer_id: str,
        test_animal_id: str,
    ) -> None:
        """Returns all sales created by the user."""
        for i in range(3):
            await client.post(
                "/market/sales",
                json={
                    "animal_id": test_animal_id,
                    "buyer_id": test_buyer_id,
                    "sale_date": f"2024-0{i + 1}-15",
                    "price": 1000.0 + i * 100,
                    "price_per_kg": 10.0 + i,
                    "weight": 100.0 + i * 10,
                    "description": f"Venta {i + 1}",
                },
            )

        response = await client.get("/market/sales")

        assert response.status_code == 200
        sales = response.json()
        assert len(sales) == 3


@pytest.mark.asyncio
class TestDeleteSaleIntegration:
    """DELETE /market/sales/{id} — delete a sale."""

    async def test_delete_sale_returns_204(
        self,
        client: AsyncClient,
        test_buyer_id: str,
        test_animal_id: str,
    ) -> None:
        """Deleting an existing sale returns 204 No Content."""
        create_resp = await client.post(
            "/market/sales",
            json={
                "animal_id": test_animal_id,
                "buyer_id": test_buyer_id,
                "sale_date": "2024-06-15",
                "price": 1500.00,
                "price_per_kg": 12.50,
                "weight": 120.0,
            },
        )
        sale_id = create_resp.json()["id"]

        response = await client.delete(f"/market/sales/{sale_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_resp = await client.get(f"/market/sales/{sale_id}")
        assert get_resp.status_code == 404

    async def test_delete_nonexistent_sale_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Deleting a non-existent sale returns 404."""
        from uuid import uuid4

        response = await client.delete(f"/market/sales/{uuid4()}")

        assert response.status_code == 404
