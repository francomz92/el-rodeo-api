"""Unit tests for animal supply type domain services."""

from uuid import UUID

import pytest
from tests.factories import (
    make_supply_type_create,
    make_supply_type_entity,
    make_supply_type_list_params,
    make_supply_type_update,
)

from src.common.domain.exceptions import BusinessValidationError, ConflictError, NotFoundError
from src.finance.domain.services.animal_supply_type_services.create_animal_supply_type_service import (
    CreateAnimalSupplyTypeService,
)
from src.finance.domain.services.animal_supply_type_services.delete_animal_supply_type_service import (
    DeleteAnimalSupplyTypeService,
)
from src.finance.domain.services.animal_supply_type_services.get_animal_supply_type_service import (
    GetSupplyTypeService,
)
from src.finance.domain.services.animal_supply_type_services.list_animal_supply_type_service import (
    ListAnimalSupplyTypeService,
)
from src.finance.domain.services.animal_supply_type_services.update_animal_supply_type_service import (
    UpdateAnimalSupplyTypeService,
)


class TestCreateAnimalSupplyTypeService:
    """CreateAnimalSupplyTypeService creates new supply types."""

    def setup_method(self) -> None:
        self.service = CreateAnimalSupplyTypeService()

    async def test_validate_duplicated_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_name.return_value = None

        await self.service.validate_duplicated(make_supply_type_create(), repo)

    async def test_validate_duplicated_raises_when_exists(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_name.return_value = make_supply_type_entity()

        with pytest.raises(ConflictError):
            await self.service.validate_duplicated(make_supply_type_create(), repo)

    async def test_create_new_returns_entity(self) -> None:
        from unittest.mock import AsyncMock

        data = make_supply_type_create()
        expected = make_supply_type_entity()
        repo = AsyncMock()
        repo.create.return_value = expected

        result = await self.service.create_new(data, repo)

        assert result == expected
        repo.create.assert_awaited_once_with(data)


class TestGetSupplyTypeService:
    """GetSupplyTypeService validates supply type existence."""

    def setup_method(self) -> None:
        self.service = GetSupplyTypeService()

    async def test_validate_exists_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = True

        await self.service.validate_exists(
            UUID("00000000-0000-0000-0000-000000000001"),
            repo,
        )

    async def test_validate_exists_raises_when_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = False

        with pytest.raises(BusinessValidationError):
            await self.service.validate_exists(
                UUID("00000000-0000-0000-0000-000000000001"),
                repo,
            )


class TestListAnimalSupplyTypeService:
    """ListAnimalSupplyTypeService lists supply types."""

    def setup_method(self) -> None:
        self.service = ListAnimalSupplyTypeService()

    async def test_get_supply_types_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        filters = make_supply_type_list_params()
        expected = [make_supply_type_entity(), make_supply_type_entity()]
        repo = AsyncMock()
        repo.list.return_value = expected

        result = await self.service.get_supply_types(
            filters=filters,
            limit=10,
            offset=0,
            order_by="name",
            repository=repo,
        )

        assert result == expected
        repo.list.assert_awaited_once_with(filters=filters, limit=10, offset=0, order_by="name")


class TestUpdateAnimalSupplyTypeService:
    """UpdateAnimalSupplyTypeService updates a supply type."""

    def setup_method(self) -> None:
        self.service = UpdateAnimalSupplyTypeService()

    async def test_validate_exists_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = make_supply_type_entity()

        await self.service.validate_exists(
            UUID("00000000-0000-0000-0000-000000000001"),
            repo,
        )

    async def test_validate_exists_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.validate_exists(
                UUID("00000000-0000-0000-0000-000000000001"),
                repo,
            )

    async def test_validate_duplicated_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_name.return_value = None

        await self.service.validate_duplicated(make_supply_type_update(), repo)

    async def test_validate_duplicated_raises_when_exists(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_name.return_value = make_supply_type_entity()

        with pytest.raises(ConflictError):
            await self.service.validate_duplicated(make_supply_type_update(), repo)

    async def test_update_supply_type_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        type_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_supply_type_update()
        expected = make_supply_type_entity(id=type_id)
        repo = AsyncMock()
        repo.update.return_value = expected

        result = await self.service.update_supply_type(type_id, data, repo)

        assert result == expected
        repo.update.assert_awaited_once_with(type_id, data)


class TestDeleteAnimalSupplyTypeService:
    """DeleteAnimalSupplyTypeService deletes a supply type."""

    def setup_method(self) -> None:
        self.service = DeleteAnimalSupplyTypeService()

    async def test_validate_exists_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = True

        await self.service.validate_exists(
            UUID("00000000-0000-0000-0000-000000000001"),
            repo,
        )

    async def test_validate_exists_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = False

        with pytest.raises(NotFoundError):
            await self.service.validate_exists(
                UUID("00000000-0000-0000-0000-000000000001"),
                repo,
            )

    async def test_delete_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        type_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = AsyncMock()

        await self.service.delete(type_id, repo)

        repo.delete.assert_awaited_once_with(type_id)
