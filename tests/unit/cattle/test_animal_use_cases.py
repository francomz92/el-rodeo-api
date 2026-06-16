"""Unit tests for animal use cases.

NOTE: RegisterAnimalCase has async def __init__ (a codebase issue), so
it cannot be instantiated directly in tests. We test the remaining
use cases that use normal __init__.
"""

from uuid import UUID

import pytest
from tests.factories import (
    make_animal_entity,
    make_animal_list_params,
    make_animal_update,
)
from tests.mocks import MockUoW

from src.cattle.application.uses_cases.animals_use_cases.delete_animal_case import (
    DeleteAnimalCase,
)
from src.cattle.application.uses_cases.animals_use_cases.get_animal_case import (
    ObtainAnimalCase,
)
from src.cattle.application.uses_cases.animals_use_cases.list_animals_case import (
    ListAnimalsCase,
)
from src.cattle.application.uses_cases.animals_use_cases.update_animal_case import (
    UpdateAnimalCase,
)
from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.services.animals.delete_animal_service import DeleteAnimalService
from src.cattle.domain.services.animals.get_animal_service import GetAnimalService
from src.cattle.domain.services.animals.list_animal_service import ListAnimalService
from src.cattle.domain.services.animals.update_animal_service import UpdateAnimalService
from src.common.domain.exceptions import ConflictError, NotFoundError, NotPermissionError


class TestObtainAnimalCase:
    """ObtainAnimalCase retrieves a single animal."""

    def setup_method(self) -> None:
        self.service = GetAnimalService()
        self.uow = MockUoW()
        self.case = ObtainAnimalCase(uow=self.uow, service=self.service)

    async def test_execute_returns_animal(self) -> None:
        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        expected_entity = make_animal_entity(id=animal_id)
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = expected_entity

        result = await self.case.execute(id=animal_id, user_id=user_id)

        assert result == expected_entity
        repo.get_by_id.assert_awaited_once_with(id=animal_id, user_id=user_id)

    async def test_execute_raises_when_not_found(self) -> None:
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.case.execute(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                user_id=UUID("00000000-0000-0000-0000-000000000002"),
            )


class TestListAnimalsCase:
    """ListAnimalsCase lists animals for a user."""

    def setup_method(self) -> None:
        self.service = ListAnimalService()
        self.uow = MockUoW()
        self.case = ListAnimalsCase(uow=self.uow, service=self.service)

    async def test_execute_returns_animal_list(self) -> None:
        user_id = UUID("00000000-0000-0000-0000-000000000001")
        expected_entities = [make_animal_entity(), make_animal_entity()]
        filters = make_animal_list_params()
        repo = self.uow.get_repository(IAnimalsRepository)
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


class TestUpdateAnimalCase:
    """UpdateAnimalCase updates an animal after validating existence."""

    def setup_method(self) -> None:
        self.service = UpdateAnimalService()
        self.uow = MockUoW()
        self.case = UpdateAnimalCase(uow=self.uow, service=self.service)

    async def test_execute_updates_animal_successfully(self) -> None:
        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_update()
        existing = make_animal_entity(id=animal_id)
        updated = make_animal_entity(id=animal_id)
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = existing
        repo.update_data.return_value = updated

        result = await self.case.execute(id=animal_id, data=data)

        assert result == updated
        repo.update_data.assert_awaited_once()
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_when_not_found(self) -> None:
        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_update()
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.case.execute(id=animal_id, data=data)

        repo.update_data.assert_not_called()
        self.uow.commit.assert_not_called()

    async def test_execute_raises_when_sold(self) -> None:
        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_update()
        sold_animal = make_animal_entity(id=animal_id, status=AnimalStatus.SOLD)
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = sold_animal

        with pytest.raises(NotPermissionError):
            await self.case.execute(id=animal_id, data=data)

        repo.update_data.assert_not_called()
        self.uow.commit.assert_not_called()


class TestDeleteAnimalCase:
    """DeleteAnimalCase deletes an animal after validation."""

    def setup_method(self) -> None:
        self.service = DeleteAnimalService()
        self.uow = MockUoW()
        self.case = DeleteAnimalCase(uow=self.uow, service=self.service)

    async def test_execute_deletes_animal(self) -> None:
        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        existing = make_animal_entity(id=animal_id)
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = existing

        await self.case.execute(id=animal_id, user_id=user_id)

        repo.delete.assert_awaited_once_with(id=animal_id)
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_when_not_found(self) -> None:
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.case.execute(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                user_id=UUID("00000000-0000-0000-0000-000000000002"),
            )

        repo.delete.assert_not_called()
        self.uow.commit.assert_not_called()

    async def test_execute_raises_when_sold(self) -> None:
        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        sold = make_animal_entity(id=animal_id, status=AnimalStatus.SOLD)
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = sold

        with pytest.raises(ConflictError):
            await self.case.execute(id=animal_id, user_id=user_id)

        repo.delete.assert_not_called()
        self.uow.commit.assert_not_called()
