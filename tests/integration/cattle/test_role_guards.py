"""Integration tests for role guard enforcement in the cattle context.

Verifies that the require_role dependency correctly enforces role hierarchy
on all cattle endpoints:
  - /animals: router-level VIEWER, create/update → EDITOR, delete → ADMIN
  - /animal-protocols: router-level VIEWER, update → EDITOR, delete → ADMIN
  - /animal-types: create/update → ADMIN, list is public
  - /schedule-events: router-level VIEWER, create/update → EDITOR, delete → ADMIN
"""

from uuid import uuid4

from httpx import AsyncClient

# ── Tests: /animals role guards ───────────────────────────────────────


class TestAnimalsRoleGuards:
    """Route-level VIEWER, POST/PUT → EDITOR, DELETE → ADMIN."""

    ANIMALS_PATH = "/cattle/animals"

    async def test_viewer_list_animals(self, viewer_client: AsyncClient, test_animal_type_id: str) -> None:
        """VIEWER can list animals (router-level guard)."""
        response = await viewer_client.get(self.ANIMALS_PATH)
        assert response.status_code == 200

    async def test_viewer_create_animal_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on create animal (EDITOR required)."""
        response = await viewer_client.post(self.ANIMALS_PATH, json={})
        assert response.status_code == 403

    async def test_viewer_update_animal_returns_403(self, viewer_client: AsyncClient, test_animal_type_id: str) -> None:
        """VIEWER gets 403 on update animal (EDITOR required)."""
        response = await viewer_client.put(f"{self.ANIMALS_PATH}/{uuid4()}", json={})
        assert response.status_code == 403

    async def test_viewer_delete_animal_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on delete animal (ADMIN required)."""
        response = await viewer_client.delete(f"{self.ANIMALS_PATH}/{uuid4()}")
        assert response.status_code == 403

    async def test_editor_create_animal_not_403(self, editor_client: AsyncClient) -> None:
        """EDITOR is NOT denied on create animal (should pass guard)."""
        response = await editor_client.post(self.ANIMALS_PATH, json={})
        # Guard passes → we get 422 (validation) instead of 403
        assert response.status_code != 403

    async def test_editor_update_animal_not_403(self, editor_client: AsyncClient) -> None:
        """EDITOR is NOT denied on update animal."""
        response = await editor_client.put(f"{self.ANIMALS_PATH}/{uuid4()}", json={})
        assert response.status_code != 403

    async def test_editor_delete_animal_returns_403(self, editor_client: AsyncClient) -> None:
        """EDITOR gets 403 on delete animal (ADMIN required)."""
        response = await editor_client.delete(f"{self.ANIMALS_PATH}/{uuid4()}")
        assert response.status_code == 403

    async def test_admin_delete_animal_not_403(self, admin_role_client: AsyncClient) -> None:
        """ADMIN is NOT denied on delete animal (guard passes)."""
        response = await admin_role_client.delete(f"{self.ANIMALS_PATH}/{uuid4()}")
        assert response.status_code != 403


# ── Tests: /animal-protocols role guards ──────────────────────────────


class TestAnimalProtocolsRoleGuards:
    """Route-level VIEWER, PUT → EDITOR, DELETE → ADMIN."""

    PROTOCOLS_PATH = "/cattle/animal-protocols"

    async def test_viewer_list_protocols(self, viewer_client: AsyncClient) -> None:
        """VIEWER can list protocols (router-level guard)."""
        response = await viewer_client.get(self.PROTOCOLS_PATH)
        assert response.status_code == 200

    async def test_viewer_get_protocol(self, viewer_client: AsyncClient) -> None:
        """VIEWER can get a protocol by id (router-level guard)."""
        response = await viewer_client.get(f"{self.PROTOCOLS_PATH}/{uuid4()}")
        assert response.status_code == 404  # guard passes, resource missing

    async def test_viewer_update_protocol_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on update protocol (EDITOR required)."""
        response = await viewer_client.put(f"{self.PROTOCOLS_PATH}/{uuid4()}", json={})
        assert response.status_code == 403

    async def test_viewer_delete_protocol_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on delete protocol (ADMIN required)."""
        response = await viewer_client.delete(f"{self.PROTOCOLS_PATH}/{uuid4()}")
        assert response.status_code == 403

    async def test_editor_update_protocol_not_403(self, editor_client: AsyncClient) -> None:
        """EDITOR is NOT denied on update protocol."""
        response = await editor_client.put(f"{self.PROTOCOLS_PATH}/{uuid4()}", json={})
        assert response.status_code != 403

    async def test_editor_delete_protocol_returns_403(self, editor_client: AsyncClient) -> None:
        """EDITOR gets 403 on delete protocol (ADMIN required)."""
        response = await editor_client.delete(f"{self.PROTOCOLS_PATH}/{uuid4()}")
        assert response.status_code == 403


# ── Tests: /schedule-events role guards ───────────────────────────────


class TestScheduleEventsRoleGuards:
    """Route-level VIEWER, POST/PUT → EDITOR, DELETE → ADMIN."""

    EVENTS_PATH = "/cattle/schedule-events"

    async def test_viewer_list_events(self, viewer_client: AsyncClient) -> None:
        """VIEWER can list events (router-level guard)."""
        response = await viewer_client.get(self.EVENTS_PATH)
        assert response.status_code == 200

    async def test_viewer_create_event_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on create event (EDITOR required)."""
        response = await viewer_client.post(self.EVENTS_PATH, json={})
        assert response.status_code == 403

    async def test_viewer_delete_event_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on delete event (ADMIN required)."""
        response = await viewer_client.delete(f"{self.EVENTS_PATH}/{uuid4()}")
        assert response.status_code == 403

    async def test_editor_create_event_not_403(self, editor_client: AsyncClient) -> None:
        """EDITOR is NOT denied on create event."""
        response = await editor_client.post(self.EVENTS_PATH, json={})
        assert response.status_code != 403

    async def test_editor_delete_event_returns_403(self, editor_client: AsyncClient) -> None:
        """EDITOR gets 403 on delete event (ADMIN required)."""
        response = await editor_client.delete(f"{self.EVENTS_PATH}/{uuid4()}")
        assert response.status_code == 403


# ── Tests: /animal-types role guards ──────────────────────────────────


class TestAnimalTypesRoleGuards:
    """All CRUD operations → ADMIN only."""

    TYPES_PATH = "/cattle/animal-types"

    async def test_viewer_list_animal_types_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on list (ADMIN required)."""
        response = await viewer_client.get(self.TYPES_PATH)
        assert response.status_code == 403

    async def test_viewer_create_animal_type_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on create (ADMIN required)."""
        response = await viewer_client.post(self.TYPES_PATH, json={})
        assert response.status_code == 403

    async def test_viewer_update_animal_type_returns_403(self, viewer_client: AsyncClient) -> None:
        """VIEWER gets 403 on update (ADMIN required)."""
        response = await viewer_client.put(f"{self.TYPES_PATH}/{uuid4()}", json={})
        assert response.status_code == 403

    async def test_editor_create_animal_type_returns_403(self, editor_client: AsyncClient) -> None:
        """EDITOR gets 403 on create (ADMIN required)."""
        response = await editor_client.post(self.TYPES_PATH, json={})
        assert response.status_code == 403

    async def test_admin_create_animal_type_not_403(self, admin_role_client: AsyncClient) -> None:
        """ADMIN is NOT denied on create animal type."""
        response = await admin_role_client.post(self.TYPES_PATH, json={})
        assert response.status_code != 403

    async def test_admin_update_animal_type_not_403(self, admin_role_client: AsyncClient) -> None:
        """ADMIN is NOT denied on update animal type."""
        response = await admin_role_client.put(f"{self.TYPES_PATH}/{uuid4()}", json={})
        assert response.status_code != 403
