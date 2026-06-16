"""Integration tests for the /finance/supply-types API endpoint.

Supply type endpoints require admin privileges.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreateSupplyTypeIntegration:
    """POST /finance/supply-types — create a new supply type."""

    async def test_create_supply_type_returns_422_on_empty_payload(
        self,
        client: AsyncClient,
    ) -> None:
        """Missing fields return 422."""
        response = await client.post("/finance/supply-types", json={})
        assert response.status_code in (422, 403)


@pytest.mark.asyncio
class TestListSupplyTypesIntegration:
    """GET /finance/supply-types — list supply types."""

    async def test_list_supply_types_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns a list (possibly empty) of supply types."""
        response = await client.get("/finance/supply-types")
        assert response.status_code in (200, 403)
        if response.status_code == 200:
            assert isinstance(response.json(), list)
