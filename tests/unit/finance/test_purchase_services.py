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

        supply = make_purchase_entity()
        repo = AsyncMock()
        repo.get_by_id.return_value = supply

        await self.service.validate_supply(
            UUID("00000000-0000-0000-0000-000000000001"),
            repo,
        )

    async def test_validate_supply_exists_raises_when_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(BusinessValidationError):
            await self.service.validate_supply(
                UUID("00000000-0000-0000-0000-000000000001"),
                repo,
            )

    async def test_create_new_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        user_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_purchase_create()
        expected_entity = make_purchase_entity()
        repo = AsyncMock()
        repo.create.return_value = expected_entity

        result = await self.service.create_new_purchase(user_id, data, repo)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(user_id=user_id, data=data)


class TestGetPurchaseService:
    """GetPurchaseService retrieves a purchase."""

    def setup_method(self) -> None:
        self.service = GetPurchaseService()

    async def test_get_purchase_returns_entity(self) -> None:
        from unittest.mock import AsyncMock

        purchase_id = UUID("00000000-0000-0000-0000-000000000001")
        expected_entity = make_purchase_entity(id=purchase_id)
        repo = AsyncMock()
        repo.get_by_id.return_value = expected_entity

        result = await self.service.validate_existence(purchase_id, repo)

        assert result == expected_entity
        repo.get_by_id.assert_awaited_once_with(id=purchase_id)

    async def test_get_purchase_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.validate_existence(
                UUID("00000000-0000-0000-0000-000000000001"),
                repo,
            )


class TestListPurchaseService:
    """ListPurchaseService lists purchases."""

    def setup_method(self) -> None:
        self.service = ListPurchaseService()

    async def test_list_purchases_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        filters = make_purchase_list_params()
        expected = [make_purchase_entity(), make_purchase_entity()]
        repo = AsyncMock()
        repo.list_for_user.return_value = expected

        result = await self.service.get_purchases(
            repository=repo,
            query=filters,
            limit=10,
            offset=0,
            order_by="purchase_date",
        )

        assert result == expected
        repo.list_for_user.assert_awaited_once_with(
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

        purchase = make_purchase_entity()
        repo = AsyncMock()
        repo.get_by_id.return_value = purchase

        await self.service.validate_existence(
            UUID("00000000-0000-0000-0000-000000000001"),
            repo,
        )

    async def test_validate_purchase_exists_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.validate_existence(
                UUID("00000000-0000-0000-0000-000000000001"),
                repo,
            )

    async def test_delete_purchase_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        purchase_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = AsyncMock()

        await self.service.delete_purchase(purchase_id, repo)

        repo.delete.assert_awaited_once_with(id=purchase_id)
