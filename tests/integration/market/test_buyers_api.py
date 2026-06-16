"""Integration tests for the /market/buyers API endpoint.

Each test runs against a real test database with full stack:
  router → use case → domain service → repository → SQLAlchemy → asyncpg

Fixtures provide:
  - An authenticated test user
  - Clean database tables (session-scoped, per-function isolation via NullPool)
"""

from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreateBuyerIntegration:
    """POST /market/buyers — create a new buyer."""

    async def test_create_buyer_returns_201(
        self,
        client: AsyncClient,
    ) -> None:
        """A valid buyer creation returns 201 with the created buyer data."""
        payload = {
            "name": "Comprador Test",
            "description": "Comprador de prueba",
            "contact_number": "1234567890",
            "contact_address": "Calle Falsa 123",
        }

        response = await client.post("/market/buyers", json=payload)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        body = response.json()
        assert body["name"] == "Comprador Test"
        assert body["description"] == "Comprador de prueba"
        assert body["contact_number"] == "1234567890"
        assert body["contact_address"] == "Calle Falsa 123"
        assert isinstance(UUID(body["id"]), UUID)

    async def test_create_buyer_returns_422_on_empty_payload(
        self,
        client: AsyncClient,
    ) -> None:
        """Missing required fields return 422."""
        response = await client.post("/market/buyers", json={})

        assert response.status_code == 422

    async def test_create_buyer_returns_422_on_missing_fields(
        self,
        client: AsyncClient,
    ) -> None:
        """Only name is required; missing it returns 422."""
        response = await client.post(
            "/market/buyers",
            json={"description": "solo descripcion"},
        )

        assert response.status_code == 422


@pytest.mark.asyncio
class TestGetBuyerIntegration:
    """GET /market/buyers/{id} — retrieve a single buyer."""

    async def test_get_buyer_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns the buyer data when the buyer exists."""
        create_resp = await client.post(
            "/market/buyers",
            json={
                "name": "Comprador Test",
                "description": "Comprador de prueba",
                "contact_number": "1234567890",
                "contact_address": "Calle Falsa 123",
            },
        )
        buyer_id = create_resp.json()["id"]

        response = await client.get(f"/market/buyers/{buyer_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == buyer_id
        assert body["name"] == "Comprador Test"

    async def test_get_nonexistent_buyer_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing buyer."""
        from uuid import uuid4

        response = await client.get(f"/market/buyers/{uuid4()}")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestListBuyersIntegration:
    """GET /market/buyers — list buyers for the authenticated user."""

    async def test_list_buyers_is_empty_initially(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns an empty list when there are no buyers for this user."""
        response = await client.get("/market/buyers")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_buyers_returns_created_buyers(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns all buyers created by the user."""
        for i in range(3):
            await client.post(
                "/market/buyers",
                json={
                    "name": f"Comprador {i + 1}",
                    "description": f"Descripcion {i + 1}",
                    "contact_number": f"123456789{i}",
                    "contact_address": f"Direccion {i + 1}",
                },
            )

        response = await client.get("/market/buyers")

        assert response.status_code == 200
        buyers = response.json()
        assert len(buyers) == 3


@pytest.mark.asyncio
class TestUpdateBuyerIntegration:
    """PUT /market/buyers/{id} — update a buyer."""

    async def test_update_buyer_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Updating an existing buyer returns the updated data."""
        create_resp = await client.post(
            "/market/buyers",
            json={
                "name": "Nombre Original",
                "description": "Descripcion original",
                "contact_number": "1111111111",
                "contact_address": "Direccion original",
            },
        )
        buyer_id = create_resp.json()["id"]

        response = await client.put(
            f"/market/buyers/{buyer_id}",
            json={
                "name": "Nombre Actualizado",
                "description": "Descripcion actualizada",
                "contact_number": "2222222222",
                "contact_address": "Direccion actualizada",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Nombre Actualizado"
        assert body["description"] == "Descripcion actualizada"
        assert body["contact_number"] == "2222222222"
        assert body["contact_address"] == "Direccion actualizada"

    async def test_update_nonexistent_buyer_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Updating a non-existent buyer returns 404."""
        from uuid import uuid4

        response = await client.put(
            f"/market/buyers/{uuid4()}",
            json={
                "name": "Nadie",
                "description": "No existe",
                "contact_number": "0000000000",
                "contact_address": "En ningun lado",
            },
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestDeleteBuyerIntegration:
    """DELETE /market/buyers/{id} — delete a buyer."""

    async def test_delete_buyer_returns_204(
        self,
        client: AsyncClient,
    ) -> None:
        """Deleting an existing buyer returns 204 No Content."""
        create_resp = await client.post(
            "/market/buyers",
            json={
                "name": "Comprador a eliminar",
                "description": "Sera borrado",
                "contact_number": "9999999999",
                "contact_address": "Eliminacion",
            },
        )
        buyer_id = create_resp.json()["id"]

        response = await client.delete(f"/market/buyers/{buyer_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_resp = await client.get(f"/market/buyers/{buyer_id}")
        assert get_resp.status_code == 404

    async def test_delete_nonexistent_buyer_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Deleting a non-existent buyer returns 404."""
        from uuid import uuid4

        response = await client.delete(f"/market/buyers/{uuid4()}")

        assert response.status_code == 404
