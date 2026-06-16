"""Unit tests for purchase use cases."""

from uuid import UUID

import pytest
from tests.factories import (
    make_purchase_create,
    make_purchase_entity,
    make_purchase_list_params,
)
from tests.mocks import MockUoW

from src.common.domain.exceptions import NotFoundError
from src.finance.application.uses_cases.purchase_cases.create_purchase_case import (
    CreatePurchaseCase,
)
from src.finance.application.uses_cases.purchase_cases.delete_purchase_case import (
    DeletePurchaseCase,
)
from src.finance.application.uses_cases.purchase_cases.get_purchase_case import (
    GetPurchaseCase,
)
from src.finance.application.uses_cases.purchase_cases.list_purchase_case import (
    ListPurchaseCase,
)
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.services.purchase_services.create_purchase_service import (
    CreatePurchaseService,
)
from src.finance.domain.services.purchase_services.delete_purchase_service import (
    DeletePurchaseService,
)
from src.finance.domain.services.purchase_services.get_purchase_service import (
    GetPurchaseService,
)
from src.finance.domain.services.purchase_services.list_purchase_service import (
    ListPurchaseService,
)


class TestCreatePurchaseCase:
    """CreatePurchaseCase creates a purchase via UoW."""

    def setup_method(self) -> None:
        self.service = CreatePurchaseService()
        self.uow = MockUoW()
        self.case = CreatePurchaseCase(uow=self.uow, service=self.service)

    async def test_execute_creates_purchase_successfully(self) -> None:
        from datetime import date

        data = make_purchase_create(
            amount=10.0,
            price=1000.0,
            unit_price=100.0,
            purchase_date=date(2024, 6, 15),
        )
        expected = make_purchase_entity()
        repo = self.uow.get_repository(IPurchasesRepository)
        supply_repo = self.uow.get_repository(IAnimalSuppliesRepository)
        repo.create.return_value = expected
        supply_repo.exists.return_value = True

        result = await self.case.execute(data=data)

        assert result == expected
        repo.create.assert_awaited_once()
        supply_repo.increase_stock.assert_awaited_once()
        self.uow.commit.assert_awaited_once()


class TestGetPurchaseCase:
    """GetPurchaseCase retrieves a purchase."""

    def setup_method(self) -> None:
        self.service = GetPurchaseService()
        self.uow = MockUoW()
        self.case = GetPurchaseCase(uow=self.uow, service=self.service)

    async def test_execute_returns_purchase(self) -> None:
        purchase_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        expected = make_purchase_entity(id=purchase_id)
        repo = self.uow.get_repository(IPurchasesRepository)
        repo.get_by_id.return_value = expected

        result = await self.case.execute(id=purchase_id, user_id=user_id)

        assert result == expected
        repo.get_by_id.assert_awaited_once_with(purchase_id, user_id)

    async def test_execute_raises_when_not_found(self) -> None:
        repo = self.uow.get_repository(IPurchasesRepository)
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.case.execute(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                user_id=UUID("00000000-0000-0000-0000-000000000002"),
            )


class TestListPurchaseCase:
    """ListPurchaseCase lists purchases."""

    def setup_method(self) -> None:
        self.service = ListPurchaseService()
        self.uow = MockUoW()
        self.case = ListPurchaseCase(uow=self.uow, service=self.service)

    async def test_execute_returns_list(self) -> None:
        user_id = UUID("00000000-0000-0000-0000-000000000001")
        filters = make_purchase_list_params()
        expected = [make_purchase_entity(), make_purchase_entity()]
        repo = self.uow.get_repository(IPurchasesRepository)
        repo.list_for_user.return_value = expected

        result = await self.case.execute(
            filter=filters,
            user_id=user_id,
            limit=10,
            offset=0,
            order_by="purchase_date",
        )

        assert result == expected
        repo.list_for_user.assert_awaited_once_with(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="purchase_date",
        )


class TestDeletePurchaseCase:
    """DeletePurchaseCase deletes a purchase."""

    def setup_method(self) -> None:
        self.service = DeletePurchaseService()
        self.uow = MockUoW()
        self.case = DeletePurchaseCase(uow=self.uow, service=self.service)

    async def test_execute_deletes_purchase(self) -> None:
        purchase_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        repo = self.uow.get_repository(IPurchasesRepository)
        repo.exists.return_value = True

        await self.case.execute(id=purchase_id, user_id=user_id)

        repo.delete.assert_awaited_once_with(purchase_id)

    async def test_execute_raises_when_not_found(self) -> None:
        repo = self.uow.get_repository(IPurchasesRepository)
        repo.exists.return_value = False

        with pytest.raises(NotFoundError):
            await self.case.execute(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                user_id=UUID("00000000-0000-0000-0000-000000000002"),
            )

        repo.delete.assert_not_called()
        self.uow.commit.assert_not_called()
