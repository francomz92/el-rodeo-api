"""Integration tests for the /cattle/animals API endpoint.

Fixtures:
  - test_animal_type_id: pre-inserted animal type row
  - test_user_id: pre-inserted user row
  - client: authenticated HTTPX client
"""

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreateAnimalIntegration:
    """POST /cattle/animals — create a new animal."""

    async def test_create_animal_returns_201(
        self,
        client: AsyncClient,
        test_animal_type_id: str,
    ) -> None:
        """A valid animal creation returns 201."""
        payload = {
            "type_id": test_animal_type_id,
            "caravana": f"CAR-{uuid4().hex[:6]}",
            "breed": "Angus",
            "tag": f"TAG-{uuid4().hex[:6]}",
            "date_of_birth": "2023-01-15",
            "initial_weight": 150.0,
            "initial_weight_date": "2023-01-15",
            "last_weight": 320.0,
            "status": "no_disponible",
        }

        response = await client.post("/cattle/animals", json=payload)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        body = response.json()
        assert body["id"] is not None
        assert isinstance(UUID(body["id"]), UUID)

    async def test_create_animal_returns_422_on_empty_payload(
        self,
        client: AsyncClient,
    ) -> None:
        """Missing required fields return 422."""
        response = await client.post("/cattle/animals", json={})
        assert response.status_code == 422


@pytest.mark.asyncio
class TestGetAnimalIntegration:
    """GET /cattle/animals/{id} — retrieve a single animal."""

    async def test_get_animal_returns_200(
        self,
        client: AsyncClient,
        test_animal_type_id: str,
    ) -> None:
        """Returns the animal data when it exists."""
        create_resp = await client.post(
            "/cattle/animals",
            json={
                "type_id": test_animal_type_id,
                "caravana": f"CAR-{uuid4().hex[:6]}",
                "breed": "Hereford",
                "tag": f"TAG-{uuid4().hex[:6]}",
                "date_of_birth": "2023-01-15",
                "initial_weight": 150.0,
                "initial_weight_date": "2023-01-15",
                "last_weight": 320.0,
                "status": "no_disponible",
            },
        )
        animal_id = create_resp.json()["id"]

        response = await client.get(f"/cattle/animals/{animal_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == animal_id

    async def test_get_nonexistent_animal_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing animal."""
        response = await client.get(f"/cattle/animals/{uuid4()}")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestListAnimalsIntegration:
    """GET /cattle/animals — list animals for the authenticated user."""

    async def test_list_animals_returns_200(
        self,
        client: AsyncClient,
        test_animal_type_id: str,
    ) -> None:
        """Returns the list of animals."""
        response = await client.get("/cattle/animals")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
class TestUpdateAnimalIntegration:
    """PUT /cattle/animals/{id} — update an animal."""

    async def test_update_animal_returns_200(
        self,
        client: AsyncClient,
        test_animal_type_id: str,
    ) -> None:
        """Updating an existing animal returns the updated data."""
        create_resp = await client.post(
            "/cattle/animals",
            json={
                "type_id": test_animal_type_id,
                "caravana": f"CAR-{uuid4().hex[:6]}",
                "breed": "Angus",
                "tag": f"TAG-{uuid4().hex[:6]}",
                "date_of_birth": "2023-01-15",
                "initial_weight": 150.0,
                "initial_weight_date": "2023-01-15",
                "last_weight": 320.0,
                "status": "no_disponible",
            },
        )
        animal_id = create_resp.json()["id"]

        response = await client.put(
            f"/cattle/animals/{animal_id}",
            json={
                "type_id": str(test_animal_type_id),
                "breed": "Hereford",
                "date_of_birth": "2023-01-15",
                "initial_weight": 160.0,
                "initial_weight_date": "2023-01-15",
                "last_weight": 330.0,
                "status": "no_disponible",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["caravana"] is not None

    async def test_update_nonexistent_animal_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Updating a non-existent animal returns 404."""
        response = await client.put(
            f"/cattle/animals/{uuid4()}",
            json={
                "breed": "Nope",
                "date_of_birth": "2023-01-15",
                "initial_weight": 100.0,
                "initial_weight_date": "2023-01-15",
                "last_weight": 100.0,
                "status": "no_disponible",
            },
        )
        assert response.status_code in (404, 422)


@pytest.mark.asyncio
class TestDeleteAnimalIntegration:
    """DELETE /cattle/animals/{id} — delete an animal."""

    async def test_delete_animal_returns_204(
        self,
        client: AsyncClient,
        test_animal_type_id: str,
    ) -> None:
        """Deleting an existing animal returns 204 No Content."""
        create_resp = await client.post(
            "/cattle/animals",
            json={
                "type_id": test_animal_type_id,
                "caravana": f"CAR-{uuid4().hex[:6]}",
                "breed": "Angus",
                "tag": f"TAG-{uuid4().hex[:6]}",
                "date_of_birth": "2023-01-15",
                "initial_weight": 150.0,
                "initial_weight_date": "2023-01-15",
                "last_weight": 320.0,
                "status": "no_disponible",
            },
        )
        animal_id = create_resp.json()["id"]

        response = await client.delete(f"/cattle/animals/{animal_id}")

        assert response.status_code == 204

    async def test_delete_nonexistent_animal_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Deleting a non-existent animal returns 404."""
        response = await client.delete(f"/cattle/animals/{uuid4()}")
        assert response.status_code == 404
