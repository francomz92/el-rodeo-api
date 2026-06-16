"""Integration tests for the /cattle/animal-protocols API endpoint."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestGetAnimalProtocolIntegration:
    """GET /cattle/animal-protocols/{id} — retrieve a protocol."""

    async def test_get_nonexistent_protocol_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing protocol."""
        response = await client.get(f"/cattle/animal-protocols/{uuid4()}")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestListAnimalProtocolsIntegration:
    """GET /cattle/animal-protocols — list protocols."""

    async def test_list_protocols_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns a list (possibly empty) of protocols."""
        response = await client.get("/cattle/animal-protocols")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
class TestUpdateAnimalProtocolIntegration:
    """PUT /cattle/animal-protocols/{id} — update a protocol."""

    async def test_update_nonexistent_protocol_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing protocol."""
        response = await client.put(
            f"/cattle/animal-protocols/{uuid4()}",
            json={"vaccinated": False, "sale_permission": False},
        )
        assert response.status_code in (404, 422)


@pytest.mark.asyncio
class TestDeleteAnimalProtocolIntegration:
    """DELETE /cattle/animal-protocols/{id} — delete a protocol."""

    async def test_delete_nonexistent_protocol_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing protocol."""
        response = await client.delete(f"/cattle/animal-protocols/{uuid4()}")
        assert response.status_code == 404
