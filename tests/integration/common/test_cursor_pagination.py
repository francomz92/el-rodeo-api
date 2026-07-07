"""Integration tests for cursor-based pagination.

Tests both the cattle animals and auth users endpoints.
Verifies cursor pagination gives correct results AND old offset/limit still works.
"""

import warnings
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.common.infrastructure.adapters.http.output.cursor_page import (
    decode_cursor,
    encode_cursor,
)

# ── CursorPage unit helpers ──────────────────────────────────────────


class TestCursorHelpers:
    """Unit tests for cursor encode/decode."""

    def test_encode_decode_roundtrip(self) -> None:
        """Base64 encode/decode roundtrip preserves id and sort_value."""
        cursor = encode_cursor(id="abc-123", sort_value="def-456")
        decoded = decode_cursor(cursor)
        assert decoded["id"] == "abc-123"
        assert decoded["sort_value"] == "def-456"

    def test_encode_without_sort_value(self) -> None:
        """Without sort_value, id is used for both."""
        cursor = encode_cursor(id="abc-123")
        decoded = decode_cursor(cursor)
        assert decoded["id"] == "abc-123"
        assert decoded["sort_value"] == "abc-123"

    def test_decode_invalid_token_raises(self) -> None:
        """Malformed cursor raises ValueError."""
        with pytest.raises(ValueError, match="Invalid cursor"):
            decode_cursor("not-base64!!!")

    def test_cursor_is_opaque(self) -> None:
        """Cursor does not expose raw DB internals."""
        cursor = encode_cursor(id="some-id", sort_value="some-value")
        # Base64 encoding is opaque; the raw id is not visible
        assert "some-id" not in cursor


class TestOffsetDeprecationWarning:
    """Deprecation warning on offset usage in StandardQueryParams."""

    def test_offset_triggers_deprecation_warning(self) -> None:
        """Using offset!=0 without cursor emits DeprecationWarning."""
        from src.common.infrastructure.adapters.http.input.query_params import (
            StandardQueryParams,
        )

        with pytest.warns(DeprecationWarning, match="offset pagination is deprecated"):
            StandardQueryParams(offset=1, limit=10)

    def test_cursor_supresses_deprecation_warning(self) -> None:
        """Using cursor does NOT emit deprecation warning even with offset."""
        from src.common.infrastructure.adapters.http.input.query_params import (
            StandardQueryParams,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("error")  # elevate warnings to errors
            StandardQueryParams(offset=1, limit=10, cursor="some-cursor")

    def test_default_offset_no_warning(self) -> None:
        """Default offset=0 does NOT emit deprecation warning."""
        from src.common.infrastructure.adapters.http.input.query_params import (
            StandardQueryParams,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            StandardQueryParams(limit=10)


# ── Animal cursor pagination integration ─────────────────────────────


@pytest.mark.asyncio
class TestAnimalCursorPagination:
    """Cursor-based pagination on GET /cattle/animals."""

    async def _create_animals(
        self,
        client: AsyncClient,
        test_animal_type_id: str,
        count: int,
    ) -> list[str]:
        """POST *count* animals via API and return their IDs in creation order."""
        ids: list[str] = []
        for i in range(count):
            payload = {
                "type_id": test_animal_type_id,
                "caravana": f"CRS-{uuid4().hex[:6]}-{i}",
                "breed": "CursorBreed",
                "tag": f"TAG-{uuid4().hex[:6]}-{i}",
                "date_of_birth": "2023-01-15",
                "initial_weight": 150.0 + i,
                "initial_weight_date": "2023-01-15",
            }
            resp = await client.post("/cattle/animals", json=payload)
            assert resp.status_code == 201, f"Animal creation failed: {resp.text}"
            ids.append(resp.json()["id"])
        return ids

    async def test_cursor_pagination_returns_items_and_next_cursor(
        self,
        client: AsyncClient,
        test_animal_type_id: str,
    ) -> None:
        """First page returns items and a non-null next_cursor."""
        await self._create_animals(client, test_animal_type_id, count=15)

        # Start with an empty cursor (id=0) to get the first page
        cursor = encode_cursor("00000000-0000-0000-0000-000000000000")
        response = await client.get(
            "/cattle/animals",
            params={"cursor": cursor, "limit": 5},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert "items" in body
        assert "next_cursor" in body
        assert "total" in body
        assert body["next_cursor"] is not None, "Expected a next_cursor for page 1"
        assert body["total"] >= 15
        assert len(body["items"]) == 5, "Expected 5 items on first page"
        assert body["has_next"] is True

        # Follow the next cursor to page 2
        response2 = await client.get(
            "/cattle/animals",
            params={"cursor": body["next_cursor"], "limit": 5},
        )
        assert response2.status_code == 200, response2.text
        body2 = response2.json()
        assert len(body2["items"]) == 5, "Expected 5 items on page 2"
        assert body2["has_next"] is True

    async def test_cursor_last_page_returns_null_cursor(
        self,
        client: AsyncClient,
        test_animal_type_id: str,
    ) -> None:
        """Last page returns null next_cursor."""
        await self._create_animals(client, test_animal_type_id, count=3)

        # Get first page with cursor=0 and limit=10 (covers all 3 items)
        cursor = encode_cursor("00000000-0000-0000-0000-000000000000")
        response = await client.get(
            "/cattle/animals",
            params={"cursor": cursor, "limit": 10},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["next_cursor"] is None, "Last page should have null next_cursor"
        assert body["total"] >= 3
        assert body["has_next"] is False

    async def test_old_offset_limit_still_works(
        self,
        client: AsyncClient,
        test_animal_type_id: str,
    ) -> None:
        """Legacy offset/limit still returns a plain list."""
        await self._create_animals(client, test_animal_type_id, count=3)

        response = await client.get(
            "/cattle/animals",
            params={"offset": 0, "limit": 10},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        # Legacy: plain list (not CursorPage dict)
        assert isinstance(body, list), "offset/limit should return a list"


# ── User cursor pagination integration ───────────────────────────────


@pytest.mark.asyncio
class TestUserCursorPagination:
    """Cursor-based pagination on GET /auth/users."""

    async def test_admin_can_use_cursor_pagination(
        self,
        admin_role_client: AsyncClient,
        test_admin_role_user_id: str,
        test_viewer_user_id: str,
    ) -> None:
        """ADMIN can use cursor on GET /auth/users.

        Uses a cursor with id=0 (lowest possible) to get all users.
        """
        cursor = encode_cursor("00000000-0000-0000-0000-000000000000")
        response = await admin_role_client.get(
            "/auth/users",
            params={"cursor": cursor, "per_page": 10},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert "items" in body
        assert "next_cursor" in body
        assert "total" in body
        assert body["total"] >= 2  # admin + viewer
        assert len(body["items"]) >= 1

    async def test_admin_cursor_returns_null_on_last_page(
        self,
        admin_role_client: AsyncClient,
        test_admin_role_user_id: str,
    ) -> None:
        """Last page for users returns null next_cursor.

        Uses the highest possible UUID to guarantee we're past all real users.
        """
        cursor = encode_cursor("ffffffff-ffff-ffff-ffff-ffffffffffff")
        response = await admin_role_client.get(
            "/auth/users",
            params={"cursor": cursor, "per_page": 10},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["next_cursor"] is None, "Last page should have null next_cursor"
        assert len(body["items"]) == 0  # no items past max UUID

    async def test_old_page_per_page_still_works(
        self,
        admin_role_client: AsyncClient,
        test_admin_role_user_id: str,
    ) -> None:
        """Legacy page/per_page still returns PaginatedUsersSchema."""
        response = await admin_role_client.get(
            "/auth/users",
            params={"page": 1, "per_page": 10},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        # Legacy response has page and per_page fields
        assert "page" in body
        assert "per_page" in body
        assert "items" in body
        assert "total" in body
        assert body["page"] == 1
        assert body["per_page"] == 10
