"""Unit tests for sale use cases.

Use cases orchestrate domain services and repositories via the Unit of Work.
Here we mock the UoW to test the orchestration logic in isolation.
"""

from uuid import UUID

import pytest
from tests.factories import (
    make_sale_create,
    make_sale_entity,
    make_sale_list_params,
)
from tests.mocks import MockUoW

from src.common.domain.exceptions import BusinessValidationError, NotFoundError
from src.market.application.uses_cases.sale_cases.create_sale_case import (
    CreateSaleCase,
)
from src.market.application.uses_cases.sale_cases.delete_sale_case import (
    DeleteSaleCase,
)
from src.market.application.uses_cases.sale_cases.get_sale_case import GetSaleCase
from src.market.application.uses_cases.sale_cases.list_sale_case import ListSaleCase
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.services.sale_services.create_sale_service import (
    CreateSaleService,
)
from src.market.domain.services.sale_services.delete_sale_service import (
    DeleteSaleService,
)
from src.market.domain.services.sale_services.get_sale_service import GetSaleService
from src.market.domain.services.sale_services.list_sale_service import ListSaleService


class TestCreateSaleCase:
    """CreateSaleCase orchestrates validation + creation via UoW."""

    def setup_method(self) -> None:
        self.service = CreateSaleService()
        self.uow = MockUoW()
        self.case = CreateSaleCase(uow=self.uow, service=self.service)

    async def test_execute_creates_sale_successfully(self) -> None:
        """Happy path: valid data → repository called → entity returned."""
        data = make_sale_create(price=1000.0, price_per_kg=200.0)
        expected_entity = make_sale_entity()
        repo = self.uow.get_repository(ISalesRepository)
        repo.create.return_value = expected_entity

        result = await self.case.execute(data)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(data)

    async def test_execute_calls_commit(self) -> None:
        """A successful creation commits the transaction."""
        data = make_sale_create(price=1000.0, price_per_kg=200.0)
        repo = self.uow.get_repository(ISalesRepository)
        repo.create.return_value = make_sale_entity()

        await self.case.execute(data)

        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_on_invalid_data(self) -> None:
        """Invalid data raises BusinessValidationError without calling the repo."""
        data = make_sale_create(price=1000.0, price_per_kg=5000.0, weight=1.0)
        repo = self.uow.get_repository(ISalesRepository)

        with pytest.raises(BusinessValidationError):
            await self.case.execute(data)

        repo.create.assert_not_called()


class TestGetSaleCase:
    """GetSaleCase retrieves a single sale."""

    def setup_method(self) -> None:
        self.service = GetSaleService()
        self.uow = MockUoW()
        self.case = GetSaleCase(uow=self.uow, service=self.service)

    async def test_execute_returns_sale(self) -> None:
        """get_by_id is called and the entity is returned."""
        sale_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        expected_entity = make_sale_entity(id=sale_id)
        repo = self.uow.get_repository(ISalesRepository)
        repo.get_by_id.return_value = expected_entity

        result = await self.case.execute(id=sale_id, user_id=user_id)

        assert result == expected_entity
        repo.get_by_id.assert_awaited_once_with(sale_id, user_id)

    async def test_execute_raises_when_not_found(self) -> None:
        """Raises NotFoundError if the sale does not exist."""
        repo = self.uow.get_repository(ISalesRepository)
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.case.execute(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                user_id=UUID("00000000-0000-0000-0000-000000000002"),
            )


class TestListSaleCase:
    """ListSaleCase lists sales for a user with filters."""

    def setup_method(self) -> None:
        self.service = ListSaleService()
        self.uow = MockUoW()
        self.case = ListSaleCase(uow=self.uow, service=self.service)

    async def test_execute_returns_sale_list(self) -> None:
        """list_for_user is called with the correct parameters."""
        user_id = UUID("00000000-0000-0000-0000-000000000001")
        expected_entities = [make_sale_entity(), make_sale_entity()]
        params = make_sale_list_params()
        repo = self.uow.get_repository(ISalesRepository)
        repo.list_for_user.return_value = expected_entities

        result = await self.case.execute(
            user_id=user_id,
            filters=params,
            limit=10,
            offset=0,
            order_by="created_at",
        )

        assert result == expected_entities
        repo.list_for_user.assert_awaited_once_with(
            user_id=user_id,
            filters=params,
            limit=10,
            offset=0,
            order_by="created_at",
        )


class TestDeleteSaleCase:
    """DeleteSaleCase deletes a sale after verifying ownership."""

    def setup_method(self) -> None:
        self.service = DeleteSaleService()
        self.uow = MockUoW()
        self.case = DeleteSaleCase(uow=self.uow, service=self.service)

    async def test_execute_deletes_sale(self) -> None:
        """Deletes when the sale exists (the app code does NOT call commit)."""
        sale_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        repo = self.uow.get_repository(ISalesRepository)
        repo.exists.return_value = True

        await self.case.execute(id=sale_id, user_id=user_id)

        repo.delete.assert_awaited_once_with(sale_id)

    async def test_execute_raises_when_not_found(self) -> None:
        """Raises when the sale does not exist for this user."""
        sale_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        repo = self.uow.get_repository(ISalesRepository)
        repo.exists.return_value = False

        with pytest.raises(NotFoundError):
            await self.case.execute(id=sale_id, user_id=user_id)

        repo.delete.assert_not_called()
