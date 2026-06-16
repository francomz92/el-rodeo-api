"""Unit tests for animal type domain services."""

from uuid import UUID

import pytest
from tests.factories import (
    make_animal_type_create,
    make_animal_type_entity,
    make_animal_type_list_params,
    make_animal_type_update,
)

from src.cattle.domain.services.animal_type_services.create_animal_type_service import (
    CreateAnimalTypeService,
)
from src.cattle.domain.services.animal_type_services.list_animal_type_service import (
    ListAnimalTypeService,
)
from src.cattle.domain.services.animal_type_services.update_animal_type_service import (
    UpdateAnimalTypeService,
)
from src.common.domain.exceptions import ConflictError, NotFoundError


class TestCreateAnimalTypeService:
    """CreateAnimalTypeService creates new animal types."""

    def setup_method(self) -> None:
        self.service = CreateAnimalTypeService()

    async def test_validate_duplicated_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.list.return_value = []

        await self.service.validate_duplicated(name="Nuevo Tipo", repository=repo)

        repo.list.assert_awaited_once()

    async def test_validate_duplicated_raises_when_exists(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.list.return_value = [make_animal_type_entity()]

        with pytest.raises(ConflictError):
            await self.service.validate_duplicated(name="Tipo Existente", repository=repo)

    async def test_create_new_returns_entity(self) -> None:
        from unittest.mock import AsyncMock

        data = make_animal_type_create()
        expected_entity = make_animal_type_entity()
        repo = AsyncMock()
        repo.create.return_value = expected_entity

        result = await self.service.create_new(data, repo)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(data=data)


class TestListAnimalTypeService:
    """ListAnimalTypeService lists animal types."""

    def setup_method(self) -> None:
        self.service = ListAnimalTypeService()

    async def test_get_animal_types_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        filters = make_animal_type_list_params()
        expected = [make_animal_type_entity(), make_animal_type_entity()]
        repo = AsyncMock()
        repo.list.return_value = expected

        result = await self.service.get_animal_types(
            repository=repo,
            filters=filters,
            limit=10,
            offset=0,
            order_by="name",
        )

        assert result == expected
        repo.list.assert_awaited_once_with(filters, limit=10, offset=0, order_by="name")


class TestUpdateAnimalTypeService:
    """UpdateAnimalTypeService updates an existing animal type."""

    def setup_method(self) -> None:
        self.service = UpdateAnimalTypeService()

    async def test_validate_exists_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = True

        await self.service.validate_exists(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            repository=repo,
        )

    async def test_validate_exists_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = False

        with pytest.raises(NotFoundError):
            await self.service.validate_exists(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                repository=repo,
            )

    async def test_validate_duplicated_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.list.return_value = []

        await self.service.validate_duplicated(name="Nuevo Nombre", repository=repo)

    async def test_validate_duplicated_raises_when_exists(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.list.return_value = [make_animal_type_entity()]

        with pytest.raises(ConflictError):
            await self.service.validate_duplicated(name="Nombre Existente", repository=repo)

    async def test_update_animal_type_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        type_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_type_update()
        expected_entity = make_animal_type_entity(id=type_id)
        repo = AsyncMock()
        repo.update.return_value = expected_entity

        result = await self.service.update_animal_type(type_id, data, repo)

        assert result == expected_entity
        repo.update.assert_awaited_once_with(type_id, data)
