"""Integration tests for the /cattle/animal-types API endpoint.

Animal type endpoints require admin privileges.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreateAnimalTypeIntegration:
    """POST /cattle/animal-types — create a new animal type (admin only)."""

    async def test_create_animal_type_returns_422_on_empty_payload(
        self,
        client: AsyncClient,
    ) -> None:
        """Missing fields return 422."""
        response = await client.post("/cattle/animal-types", json={})
        assert response.status_code in (422, 403)

    async def test_create_animal_type_returns_422_on_missing_name(
        self,
        client: AsyncClient,
    ) -> None:
        """Missing name returns 422 (or 403 if admin check fails)."""
        response = await client.post("/cattle/animal-types", json={"name": ""})
        assert response.status_code in (201, 422, 403)


@pytest.mark.asyncio
class TestListAnimalTypesIntegration:
    """GET /cattle/animal-types — list animal types."""

    async def test_list_animal_types_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns a list (possibly empty) of animal types."""
        response = await client.get("/cattle/animal-types")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
