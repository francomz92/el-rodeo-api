"""Unit tests for buyer use cases.

Use cases orchestrate domain services and repositories via the Unit of Work.
Here we mock the UoW to test the orchestration logic in isolation.
"""

from uuid import UUID

import pytest
from tests.factories import make_buyer_create, make_buyer_entity, make_buyer_update
from tests.mocks import MockUoW

from src.common.domain.exceptions import NotFoundError
from src.market.application.uses_cases.buyer_cases.create_buyer_case import (
    CreateBuyerCase,
)
from src.market.application.uses_cases.buyer_cases.delete_buyer_case import (
    DeleteBuyerCase,
)
from src.market.application.uses_cases.buyer_cases.get_buyer_case import GetBuyerCase
from src.market.application.uses_cases.buyer_cases.list_buyer_case import ListBuyerCase
from src.market.application.uses_cases.buyer_cases.update_buyer_case import (
    UpdateBuyerCase,
)
from src.market.domain.repositories.buyers import IBuyersRepository
from src.market.domain.services.buyer_services.create_buyer_service import (
    CreateBuyerService,
)
from src.market.domain.services.buyer_services.delete_buyer_service import (
    DeleteBuyerService,
)
from src.market.domain.services.buyer_services.get_buyer_service import GetBuyerService
from src.market.domain.services.buyer_services.list_buyer_service import (
    ListBuyerService,
)
from src.market.domain.services.buyer_services.update_buyer_service import (
    UpdateBuyerService,
)


class TestCreateBuyerCase:
    """CreateBuyerCase creates a buyer via UoW."""

    def setup_method(self) -> None:
        self.service = CreateBuyerService()
        self.uow = MockUoW()
        self.case = CreateBuyerCase(uow=self.uow, service=self.service)

    async def test_execute_creates_buyer_successfully(self) -> None:
        """Happy path: valid data → repository called → entity returned."""
        data = make_buyer_create()
        expected_entity = make_buyer_entity()
        repo = self.uow.get_repository(IBuyersRepository)
        repo.create.return_value = expected_entity

        result = await self.case.execute(data)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(data)

    async def test_execute_calls_commit(self) -> None:
        """A successful creation commits the transaction."""
        data = make_buyer_create()
        repo = self.uow.get_repository(IBuyersRepository)
        repo.create.return_value = make_buyer_entity()

        await self.case.execute(data)

        self.uow.commit.assert_awaited_once()


class TestGetBuyerCase:
    """GetBuyerCase retrieves a single buyer."""

    def setup_method(self) -> None:
        self.service = GetBuyerService()
        self.uow = MockUoW()
        self.case = GetBuyerCase(uow=self.uow, service=self.service)

    async def test_execute_returns_buyer(self) -> None:
        """get_by_id is called and the entity is returned."""
        buyer_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        expected_entity = make_buyer_entity(id=buyer_id)
        repo = self.uow.get_repository(IBuyersRepository)
        repo.get_by_id.return_value = expected_entity

        result = await self.case.execute(id=buyer_id, user_id=user_id)

        assert result == expected_entity
        repo.get_by_id.assert_awaited_once_with(buyer_id, user_id)

    async def test_execute_raises_when_not_found(self) -> None:
        """Raises NotFoundError if the buyer does not exist."""
        repo = self.uow.get_repository(IBuyersRepository)
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.case.execute(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                user_id=UUID("00000000-0000-0000-0000-000000000002"),
            )


class TestListBuyerCase:
    """ListBuyerCase lists buyers for a user."""

    def setup_method(self) -> None:
        self.service = ListBuyerService()
        self.uow = MockUoW()
        self.case = ListBuyerCase(uow=self.uow, service=self.service)

    async def test_execute_returns_buyer_list(self) -> None:
        """list_for_user is called with the correct parameters."""
        user_id = UUID("00000000-0000-0000-0000-000000000001")
        expected_entities = [make_buyer_entity(), make_buyer_entity()]
        filters = make_buyer_update()
        repo = self.uow.get_repository(IBuyersRepository)
        repo.list_for_user.return_value = expected_entities

        result = await self.case.execute(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="name",
        )

        assert result == expected_entities
        repo.list_for_user.assert_awaited_once_with(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="name",
        )


class TestUpdateBuyerCase:
    """UpdateBuyerCase updates a buyer after verifying ownership."""

    def setup_method(self) -> None:
        self.service = UpdateBuyerService()
        self.uow = MockUoW()
        self.case = UpdateBuyerCase(uow=self.uow, service=self.service)

    async def test_execute_updates_buyer_successfully(self) -> None:
        """Validates existence + updates + commits."""
        buyer_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        data = make_buyer_update(name="Updated Name")
        expected_entity = make_buyer_entity(id=buyer_id, name="Updated Name")
        repo = self.uow.get_repository(IBuyersRepository)
        repo.exists.return_value = True
        repo.update_data.return_value = expected_entity

        result = await self.case.execute(id=buyer_id, user_id=user_id, data=data)

        assert result == expected_entity
        repo.exists.assert_awaited_once_with(buyer_id, user_id)
        repo.update_data.assert_awaited_once_with(buyer_id, user_id, data)
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_when_not_found(self) -> None:
        """Raises NotFoundError before calling update or commit."""
        buyer_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        data = make_buyer_update(name="Updated Name")
        repo = self.uow.get_repository(IBuyersRepository)
        repo.exists.return_value = False

        with pytest.raises(NotFoundError):
            await self.case.execute(id=buyer_id, user_id=user_id, data=data)

        repo.update_data.assert_not_called()
        self.uow.commit.assert_not_called()


class TestDeleteBuyerCase:
    """DeleteBuyerCase deletes a buyer after verifying ownership."""

    def setup_method(self) -> None:
        self.service = DeleteBuyerService()
        self.uow = MockUoW()
        self.case = DeleteBuyerCase(uow=self.uow, service=self.service)

    async def test_execute_deletes_buyer(self) -> None:
        """Validates existence + deletes + commits."""
        buyer_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        repo = self.uow.get_repository(IBuyersRepository)
        repo.exists.return_value = True

        await self.case.execute(id=buyer_id, user_id=user_id)

        repo.delete.assert_awaited_once_with(buyer_id)
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_when_not_found(self) -> None:
        """Raises NotFoundError before calling delete or commit."""
        buyer_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        repo = self.uow.get_repository(IBuyersRepository)
        repo.exists.return_value = False

        with pytest.raises(NotFoundError):
            await self.case.execute(id=buyer_id, user_id=user_id)

        repo.delete.assert_not_called()
        self.uow.commit.assert_not_called()
