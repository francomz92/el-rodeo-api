"""Unit tests for purchase domain services."""

from datetime import date
from uuid import UUID

import pytest
from tests.factories import (
    make_purchase_create,
    make_purchase_entity,
    make_purchase_list_params,
)

from src.common.domain.exceptions import BusinessValidationError, NotFoundError
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


class TestCreatePurchaseService:
    """CreatePurchaseService creates purchases with validation."""

    def setup_method(self) -> None:
        self.service = CreatePurchaseService()

    def test_validate_data_passes_with_valid_data(self) -> None:
        data = make_purchase_create(amount=10, price=1000, unit_price=100, purchase_date=date(2024, 6, 15))
        # Should not raise
        self.service.validate_data(data)

    def test_validate_data_raises_when_amount_zero(self) -> None:
        data = make_purchase_create(amount=0, price=1000, unit_price=100, purchase_date=date(2024, 6, 15))
        with pytest.raises(BusinessValidationError) as exc:
            self.service.validate_data(data)
        assert any(d.get("field") == "amount" for d in exc.value.details)

    def test_validate_data_raises_when_price_zero(self) -> None:
        data = make_purchase_create(amount=10, price=0, unit_price=100, purchase_date=date(2024, 6, 15))
        with pytest.raises(BusinessValidationError) as exc:
            self.service.validate_data(data)
        assert any(d.get("field") == "price" for d in exc.value.details)

    def test_validate_data_raises_when_unit_price_zero(self) -> None:
        data = make_purchase_create(amount=10, price=1000, unit_price=0, purchase_date=date(2024, 6, 15))
        with pytest.raises(BusinessValidationError) as exc:
            self.service.validate_data(data)
        assert any(d.get("field") == "unit_price" for d in exc.value.details)

    async def test_validate_supply_exists_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = True

        await self.service.validate_supply_exists(
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            repo,
        )

    async def test_validate_supply_exists_raises_when_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = False

        with pytest.raises(BusinessValidationError):
            await self.service.validate_supply_exists(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )

    async def test_create_new_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        user_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_purchase_create()
        expected_entity = make_purchase_entity()
        repo = AsyncMock()
        repo.create.return_value = expected_entity

        result = await self.service.create_new(user_id, data, repo)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(user_id, data)

    async def test_increase_supply_stock_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        supply_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = AsyncMock()

        await self.service.increase_supply_stock(supply_id, 10.0, repo)

        repo.increase_stock.assert_awaited_once_with(supply_id, 10.0)


class TestGetPurchaseService:
    """GetPurchaseService retrieves a purchase."""

    def setup_method(self) -> None:
        self.service = GetPurchaseService()

    async def test_get_purchase_returns_entity(self) -> None:
        from unittest.mock import AsyncMock

        purchase_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        expected_entity = make_purchase_entity(id=purchase_id)
        repo = AsyncMock()
        repo.get_by_id.return_value = expected_entity

        result = await self.service.get_purchase(purchase_id, user_id, repo)

        assert result == expected_entity
        repo.get_by_id.assert_awaited_once_with(purchase_id, user_id)

    async def test_get_purchase_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.get_purchase(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )


class TestListPurchaseService:
    """ListPurchaseService lists purchases."""

    def setup_method(self) -> None:
        self.service = ListPurchaseService()

    async def test_list_purchases_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        user_id = UUID("00000000-0000-0000-0000-000000000001")
        filters = make_purchase_list_params()
        expected = [make_purchase_entity(), make_purchase_entity()]
        repo = AsyncMock()
        repo.list_for_user.return_value = expected

        result = await self.service.list_purchases(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="purchase_date",
            repository=repo,
        )

        assert result == expected
        repo.list_for_user.assert_awaited_once_with(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="purchase_date",
        )


class TestDeletePurchaseService:
    """DeletePurchaseService deletes a purchase."""

    def setup_method(self) -> None:
        self.service = DeletePurchaseService()

    async def test_validate_purchase_exists_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = True

        await self.service.validate_purchase_exists(
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            repo,
        )

    async def test_validate_purchase_exists_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = False

        with pytest.raises(NotFoundError):
            await self.service.validate_purchase_exists(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )

    async def test_delete_purchase_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        purchase_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        repo = AsyncMock()

        await self.service.delete_purchase(purchase_id, user_id, repo)

        repo.delete.assert_awaited_once_with(purchase_id)
