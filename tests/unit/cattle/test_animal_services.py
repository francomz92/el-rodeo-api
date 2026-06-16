"""Unit tests for animal domain services."""

from uuid import UUID

import pytest
from tests.factories import make_animal_create, make_animal_entity, make_animal_list_params, make_animal_update

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.services.animals.delete_animal_service import DeleteAnimalService
from src.cattle.domain.services.animals.get_animal_service import GetAnimalService
from src.cattle.domain.services.animals.list_animal_service import ListAnimalService
from src.cattle.domain.services.animals.register_animal_service import RegisterAnimalService
from src.cattle.domain.services.animals.update_animal_service import UpdateAnimalService
from src.common.domain.exceptions import BusinessValidationError, ConflictError, DuplicatedError, NotFoundError, NotPermissionError


class TestRegisterAnimalService:
    """RegisterAnimalService validates duplicates, type, and creates animals."""

    def setup_method(self) -> None:
        self.service = RegisterAnimalService()

    async def test_validate_duplicate_passes_when_no_duplicate(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = False

        await self.service.validate_duplicate(
            user_id=UUID("00000000-0000-0000-0000-000000000001"),
            type_id=UUID("00000000-0000-0000-0000-000000000002"),
            caravana="CAR-001",
            repository=repo,
        )

        repo.exists.assert_awaited_once()

    async def test_validate_duplicate_raises_when_exists(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = True

        with pytest.raises(DuplicatedError):
            await self.service.validate_duplicate(
                user_id=UUID("00000000-0000-0000-0000-000000000001"),
                type_id=UUID("00000000-0000-0000-0000-000000000002"),
                caravana="CAR-001",
                repository=repo,
            )

    async def test_validate_type_exists_passes(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = True

        await self.service.validate_type_exists(
            type_id=UUID("00000000-0000-0000-0000-000000000001"),
            repository=repo,
        )

    async def test_validate_type_exists_raises_when_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.exists.return_value = False

        with pytest.raises(BusinessValidationError):
            await self.service.validate_type_exists(
                type_id=UUID("00000000-0000-0000-0000-000000000001"),
                repository=repo,
            )

    async def test_create_new_returns_entity(self) -> None:
        from unittest.mock import AsyncMock

        data = make_animal_create()
        expected_entity = make_animal_entity()
        repo = AsyncMock()
        repo.create.return_value = expected_entity

        result = await self.service.create_new(data, repo)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(data=data)


class TestGetAnimalService:
    """GetAnimalService retrieves a single animal."""

    def setup_method(self) -> None:
        self.service = GetAnimalService()

    async def test_validate_existence_and_get_animal_returns_entity(self) -> None:
        from unittest.mock import AsyncMock

        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        expected_entity = make_animal_entity(id=animal_id)
        repo = AsyncMock()
        repo.get_by_id.return_value = expected_entity

        result = await self.service.validate_existence_and_get_animal(animal_id, user_id, repo)

        assert result == expected_entity
        repo.get_by_id.assert_awaited_once_with(id=animal_id, user_id=user_id)

    async def test_raises_not_found_when_missing(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.validate_existence_and_get_animal(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )


class TestListAnimalService:
    """ListAnimalService lists animals for a user."""

    def setup_method(self) -> None:
        self.service = ListAnimalService()

    async def test_get_animals_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        user_id = UUID("00000000-0000-0000-0000-000000000001")
        filters = make_animal_list_params()
        expected = [make_animal_entity(), make_animal_entity()]
        repo = AsyncMock()
        repo.list_for_user.return_value = expected

        result = await self.service.get_animals(
            user_id=user_id,
            repository=repo,
            query=filters,
            limit=10,
            offset=0,
            order_by="name",
        )

        assert result == expected
        repo.list_for_user.assert_awaited_once_with(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="name",
        )


class TestUpdateAnimalService:
    """UpdateAnimalService updates an existing animal."""

    def setup_method(self) -> None:
        self.service = UpdateAnimalService()

    async def test_validate_existence_passes(self) -> None:
        from unittest.mock import AsyncMock

        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        animal = make_animal_entity(id=animal_id)
        repo = AsyncMock()
        repo.get_by_id.return_value = animal

        await self.service.validate_existence(animal_id, user_id, repo)

    async def test_validate_existence_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.validate_existence(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )

    async def test_validate_existence_raises_when_sold(self) -> None:
        from unittest.mock import AsyncMock

        animal = make_animal_entity(status=AnimalStatus.SOLD)
        repo = AsyncMock()
        repo.get_by_id.return_value = animal

        with pytest.raises(NotPermissionError, match="vendido"):
            await self.service.validate_existence(
                animal.id,
                UUID("00000000-0000-0000-0000-000000000001"),
                repo,
            )

    async def test_update_animal_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_update()
        expected_entity = make_animal_entity(id=animal_id)
        repo = AsyncMock()
        repo.update_data.return_value = expected_entity

        result = await self.service.update_animal(animal_id, data, repo)

        assert result == expected_entity
        repo.update_data.assert_awaited_once_with(id=animal_id, data=data)


class TestDeleteAnimalService:
    """DeleteAnimalService deletes an animal."""

    def setup_method(self) -> None:
        self.service = DeleteAnimalService()

    async def test_validate_animal_for_delete_passes(self) -> None:
        from unittest.mock import AsyncMock

        animal = make_animal_entity()
        repo = AsyncMock()
        repo.get_by_id.return_value = animal

        await self.service.validate_animal_for_delete(animal.id, UUID("00000000-0000-0000-0000-000000000001"), repo)

    async def test_validate_animal_for_delete_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.validate_animal_for_delete(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )

    async def test_validate_animal_for_delete_raises_when_sold(self) -> None:
        from unittest.mock import AsyncMock

        animal = make_animal_entity(status=AnimalStatus.SOLD)
        repo = AsyncMock()
        repo.get_by_id.return_value = animal

        with pytest.raises(ConflictError, match="vendido"):
            await self.service.validate_animal_for_delete(
                animal.id,
                UUID("00000000-0000-0000-0000-000000000001"),
                repo,
            )

    async def test_delete_animal_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = AsyncMock()

        await self.service.delete_animal(animal_id, repo)

        repo.delete.assert_awaited_once_with(id=animal_id)
