"""Unit tests for animal supply domain services."""

from uuid import UUID

import pytest
from tests.factories import (
    make_animal_supply_create,
    make_animal_supply_entity,
    make_animal_supply_list_params,
    make_animal_supply_update,
)

from src.common.domain.exceptions import BusinessValidationError, NotFoundError
from src.finance.domain.services.animal_supplies_services.create_animal_supplies_service import (
    CreateAnimalSuppliesService,
)
from src.finance.domain.services.animal_supplies_services.delete_animal_supplies_service import (
    DeleteAnimalSuppliesService,
)
from src.finance.domain.services.animal_supplies_services.get_animal_supplies_service import (
    GetAnimalSuppliesService,
)
from src.finance.domain.services.animal_supplies_services.list_animal_supplies_service import (
    ListAnimalSuppliesService,
)
from src.finance.domain.services.animal_supplies_services.update_animal_supplies_service import (
    UpdateAnimalSuppliesService,
)


class TestCreateAnimalSuppliesService:
    """CreateAnimalSuppliesService creates supplies with validation."""

    def setup_method(self) -> None:
        self.service = CreateAnimalSuppliesService()

    def test_validate_data_passes_when_critical_less_than_amount(self) -> None:
        data = make_animal_supply_create(amount=100.0, critical_amount=20.0)
        self.service.validate_data(data)

    def test_validate_data_raises_when_critical_gte_amount(self) -> None:
        data = make_animal_supply_create(amount=50.0, critical_amount=50.0)
        with pytest.raises(BusinessValidationError):
            self.service.validate_data(data)

    async def test_create_new_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        data = make_animal_supply_create()
        expected_entity = make_animal_supply_entity()
        repo = AsyncMock()
        repo.create.return_value = expected_entity

        result = await self.service.create_new(data, repo)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(data)


class TestGetAnimalSuppliesService:
    """GetAnimalSuppliesService retrieves a supply."""

    def setup_method(self) -> None:
        self.service = GetAnimalSuppliesService()

    async def test_get_animal_supplies_returns_entity(self) -> None:
        from unittest.mock import AsyncMock

        supply_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        expected = make_animal_supply_entity(id=supply_id)
        repo = AsyncMock()
        repo.get_by_id.return_value = expected

        result = await self.service.get_animal_supplies(supply_id, user_id, repo)

        assert result == expected
        repo.get_by_id.assert_awaited_once_with(supply_id, user_id)

    async def test_get_animal_supplies_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.get_animal_supplies(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )


class TestListAnimalSuppliesService:
    """ListAnimalSuppliesService lists supplies."""

    def setup_method(self) -> None:
        self.service = ListAnimalSuppliesService()

    async def test_get_animal_supplies_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        user_id = UUID("00000000-0000-0000-0000-000000000001")
        filters = make_animal_supply_list_params()
        expected = [make_animal_supply_entity(), make_animal_supply_entity()]
        repo = AsyncMock()
        repo.list_for_user.return_value = expected

        result = await self.service.get_animal_supplies(
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


class TestUpdateAnimalSuppliesService:
    """UpdateAnimalSuppliesService updates a supply."""

    def setup_method(self) -> None:
        self.service = UpdateAnimalSuppliesService()

    def test_validate_data_passes(self) -> None:
        data = make_animal_supply_update(amount=100.0, critical_amount=20.0)
        self.service.validate_data(data)

    def test_validate_data_raises_when_critical_gte_amount(self) -> None:
        data = make_animal_supply_update(amount=50.0, critical_amount=50.0)
        with pytest.raises(BusinessValidationError):
            self.service.validate_data(data)

    async def test_update_animal_supplies_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        supply_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        data = make_animal_supply_update()
        expected = make_animal_supply_entity(id=supply_id)
        repo = AsyncMock()
        repo.update_data.return_value = expected

        result = await self.service.update_animal_supplies(supply_id, user_id, data, repo)

        assert result == expected
        repo.update_data.assert_awaited_once_with(supply_id, user_id, data)


class TestDeleteAnimalSuppliesService:
    """DeleteAnimalSuppliesService deletes a supply."""

    def setup_method(self) -> None:
        self.service = DeleteAnimalSuppliesService()

    async def test_validate_exists_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = True

        await self.service.validate_exists(
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            repo,
        )

    async def test_validate_exists_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = False

        with pytest.raises(NotFoundError):
            await self.service.validate_exists(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )

    async def test_delete_animal_supplies_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        supply_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = AsyncMock()

        await self.service.delete_animal_supplies(supply_id, repo)

        repo.delete.assert_awaited_once_with(supply_id)
