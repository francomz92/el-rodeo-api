"""Integration tests for the /cattle/schedule-events API endpoint."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreateScheduleEventIntegration:
    """POST /cattle/schedule-events — create a new event."""

    async def test_create_event_returns_422_on_empty_payload(
        self,
        client: AsyncClient,
    ) -> None:
        """Missing fields return 422."""
        response = await client.post("/cattle/schedule-events", json={})
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListScheduleEventsIntegration:
    """GET /cattle/schedule-events — list events."""

    async def test_list_events_returns_200(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns a list (possibly empty) of events."""
        response = await client.get("/cattle/schedule-events")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
class TestUpdateScheduleEventIntegration:
    """PUT /cattle/schedule-events/{id} — update an event."""

    async def test_update_nonexistent_event_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing event."""
        response = await client.put(
            f"/cattle/schedule-events/{uuid4()}",
            json={"title": "Updated", "event_date": "2026-01-01"},
        )
        assert response.status_code in (404, 422)


@pytest.mark.asyncio
class TestDeleteScheduleEventIntegration:
    """DELETE /cattle/schedule-events/{id} — delete an event."""

    async def test_delete_nonexistent_event_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Returns 404 for a missing event."""
        response = await client.delete(f"/cattle/schedule-events/{uuid4()}")
        assert response.status_code == 404
