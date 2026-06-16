"""Integration tests for the /finance/animal-supplies API endpoint."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreateAnimalSupplyIntegration:
    """POST /finance/animal-supplies — create a new supply."""

    async def test_create_supply_returns_422_on_empty_payload(
        self,
        client: AsyncClient,
    ) -> None:
        """Missing fields return 422."""
        response = await client.post("/finance/animal-supplies", json={})
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListAnimalSuppliesIntegration:
    """GET /finance/animal-supplies — list supplies."""

    async def test_list_supplies_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns a list (possibly empty) of supplies."""
        response = await client.get("/finance/animal-supplies")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
class TestGetAnimalSupplyIntegration:
    """GET /finance/animal-supplies/{id} — retrieve a supply."""

    async def test_get_nonexistent_supply_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing supply."""
        response = await client.get(f"/finance/animal-supplies/{uuid4()}")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateAnimalSupplyIntegration:
    """PUT /finance/animal-supplies/{id} — update a supply."""

    async def test_update_nonexistent_supply_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing supply."""
        response = await client.put(
            f"/finance/animal-supplies/{uuid4()}",
            json={
                "type_id": str(uuid4()),
                "name": "Test Supply",
                "amount": 100.0,
                "critical_amount": 10.0,
                "unit_of_measurement": "kg",
            },
        )
        assert response.status_code in (404, 422)


@pytest.mark.asyncio
class TestDeleteAnimalSupplyIntegration:
    """DELETE /finance/animal-supplies/{id} — delete a supply."""

    async def test_delete_nonexistent_supply_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing supply."""
        response = await client.delete(f"/finance/animal-supplies/{uuid4()}")
        assert response.status_code == 404
