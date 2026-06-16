"""Unit tests for buyer domain services.

Domain services contain pure business logic with no infrastructure dependencies.
"""

from uuid import UUID

import pytest
from tests.factories import make_buyer_create, make_buyer_entity, make_buyer_update

from src.common.domain.exceptions import NotFoundError
from src.market.domain.services.buyer_services.create_buyer_service import (
    CreateBuyerService,
)
from src.market.domain.services.buyer_services.delete_buyer_service import (
    DeleteBuyerService,
)
from src.market.domain.services.buyer_services.get_buyer_service import (
    GetBuyerService,
)
from src.market.domain.services.buyer_services.list_buyer_service import (
    ListBuyerService,
)
from src.market.domain.services.buyer_services.update_buyer_service import (
    UpdateBuyerService,
)


class TestCreateBuyerService:
    """CreateBuyerService creates a new buyer."""

    def setup_method(self) -> None:
        self.service = CreateBuyerService()

    async def test_create_new_returns_entity(self) -> None:
        """create_new delegates to the repository and returns the result."""
        from unittest.mock import AsyncMock

        data = make_buyer_create()
        expected_entity = make_buyer_entity()
        repo = AsyncMock()
        repo.create = AsyncMock(return_value=expected_entity)

        result = await self.service.create_new(data, repo)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(data)


class TestGetBuyerService:
    """GetBuyerService retrieves a single buyer."""

    def setup_method(self) -> None:
        self.service = GetBuyerService()

    async def test_get_buyer_returns_entity(self) -> None:
        """Returns the buyer entity when found."""
        from unittest.mock import AsyncMock

        buyer_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        expected_entity = make_buyer_entity(id=buyer_id)
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=expected_entity)

        result = await self.service.get_buyer(
            id=buyer_id,
            user_id=user_id,
            repository=repo,
        )

        assert result == expected_entity
        repo.get_by_id.assert_awaited_once_with(buyer_id, user_id)

    async def test_get_buyer_raises_not_found(self) -> None:
        """Raises NotFoundError when buyer does not exist."""
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await self.service.get_buyer(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                user_id=UUID("00000000-0000-0000-0000-000000000002"),
                repository=repo,
            )


class TestListBuyerService:
    """ListBuyerService lists buyers for a user."""

    def setup_method(self) -> None:
        self.service = ListBuyerService()

    async def test_get_buyers_delegates_to_repo(self) -> None:
        """get_buyers passes filters and pagination to the repository."""
        from unittest.mock import AsyncMock

        user_id = UUID("00000000-0000-0000-0000-000000000001")
        filters = make_buyer_update()
        expected = [make_buyer_entity(), make_buyer_entity()]
        repo = AsyncMock()
        repo.list_for_user = AsyncMock(return_value=expected)

        result = await self.service.get_buyers(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="name",
            repository=repo,
        )

        assert result == expected
        repo.list_for_user.assert_awaited_once_with(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="name",
        )


class TestUpdateBuyerService:
    """UpdateBuyerService updates an existing buyer."""

    def setup_method(self) -> None:
        self.service = UpdateBuyerService()

    async def test_validate_buyer_exists_passes(self) -> None:
        """Does not raise when buyer exists."""
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists = AsyncMock(return_value=True)

        await self.service.validate_buyer_exists(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            user_id=UUID("00000000-0000-0000-0000-000000000002"),
            repository=repo,
        )

    async def test_validate_buyer_exists_raises_not_found(self) -> None:
        """Raises NotFoundError when buyer does not exist."""
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists = AsyncMock(return_value=False)

        with pytest.raises(NotFoundError):
            await self.service.validate_buyer_exists(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                user_id=UUID("00000000-0000-0000-0000-000000000002"),
                repository=repo,
            )

    async def test_update_buyer_delegates_to_repo(self) -> None:
        """update_buyer calls repository.update_data and returns the entity."""
        from unittest.mock import AsyncMock

        buyer_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        data = make_buyer_update(name="Updated Name")
        expected_entity = make_buyer_entity(id=buyer_id, name="Updated Name")
        repo = AsyncMock()
        repo.update_data = AsyncMock(return_value=expected_entity)

        result = await self.service.update_buyer(
            id=buyer_id,
            user_id=user_id,
            data=data,
            repository=repo,
        )

        assert result == expected_entity
        repo.update_data.assert_awaited_once_with(buyer_id, user_id, data)


class TestDeleteBuyerService:
    """DeleteBuyerService deletes a buyer."""

    def setup_method(self) -> None:
        self.service = DeleteBuyerService()

    async def test_validate_buyer_exists_passes(self) -> None:
        """Does not raise when buyer exists."""
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists = AsyncMock(return_value=True)

        await self.service.validate_buyer_exists(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            user_id=UUID("00000000-0000-0000-0000-000000000002"),
            repository=repo,
        )

    async def test_validate_buyer_exists_raises_not_found(self) -> None:
        """Raises NotFoundError when buyer does not exist."""
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists = AsyncMock(return_value=False)

        with pytest.raises(NotFoundError):
            await self.service.validate_buyer_exists(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                user_id=UUID("00000000-0000-0000-0000-000000000002"),
                repository=repo,
            )

    async def test_delete_buyer_delegates_to_repo(self) -> None:
        """delete_buyer calls repository.delete with the correct id."""
        from unittest.mock import AsyncMock

        buyer_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = AsyncMock()
        repo.delete = AsyncMock()

        await self.service.delete_buyer(id=buyer_id, repository=repo)

        repo.delete.assert_awaited_once_with(buyer_id)
