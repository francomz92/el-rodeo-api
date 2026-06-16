"""Unit tests for animal type use cases."""

from uuid import UUID

import pytest
from tests.factories import (
    make_animal_type_create,
    make_animal_type_entity,
    make_animal_type_list_params,
    make_animal_type_update,
)
from tests.mocks import MockUoW

from src.cattle.application.uses_cases.animal_type_cases.create_animal_type_case import (
    CreateAnimalTypeCase,
)
from src.cattle.application.uses_cases.animal_type_cases.list_animal_type_case import (
    ListAnimalTypeCase,
)
from src.cattle.application.uses_cases.animal_type_cases.update_animal_type_case import (
    UpdateAnimalTypeCase,
)
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
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


class TestCreateAnimalTypeCase:
    """CreateAnimalTypeCase creates an animal type via UoW."""

    def setup_method(self) -> None:
        self.service = CreateAnimalTypeService()
        self.uow = MockUoW()
        self.case = CreateAnimalTypeCase(uow=self.uow, service=self.service)

    async def test_execute_creates_type_successfully(self) -> None:
        data = make_animal_type_create()
        expected_entity = make_animal_type_entity()
        repo = self.uow.get_repository(IAnimalTypesRepository)
        repo.list.return_value = []
        repo.create.return_value = expected_entity

        result = await self.case.execute(data)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(data=data)
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_on_duplicate(self) -> None:
        data = make_animal_type_create()
        repo = self.uow.get_repository(IAnimalTypesRepository)
        repo.list.return_value = [make_animal_type_entity()]

        with pytest.raises(ConflictError):
            await self.case.execute(data)

        repo.create.assert_not_called()
        self.uow.commit.assert_not_called()


class TestListAnimalTypeCase:
    """ListAnimalTypeCase lists animal types."""

    def setup_method(self) -> None:
        self.service = ListAnimalTypeService()
        self.uow = MockUoW()
        self.case = ListAnimalTypeCase(uow=self.uow, service=self.service)

    async def test_execute_returns_type_list(self) -> None:
        expected = [make_animal_type_entity(), make_animal_type_entity()]
        filters = make_animal_type_list_params()
        repo = self.uow.get_repository(IAnimalTypesRepository)
        repo.list.return_value = expected

        result = await self.case.execute(filters=filters, limit=10, offset=0, order_by="name")

        assert result == expected
        repo.list.assert_awaited_once_with(filters, limit=10, offset=0, order_by="name")


class TestUpdateAnimalTypeCase:
    """UpdateAnimalTypeCase updates an animal type."""

    def setup_method(self) -> None:
        self.service = UpdateAnimalTypeService()
        self.uow = MockUoW()
        self.case = UpdateAnimalTypeCase(uow=self.uow, service=self.service)

    async def test_execute_updates_successfully(self) -> None:
        type_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_type_update()
        expected_entity = make_animal_type_entity(id=type_id)
        repo = self.uow.get_repository(IAnimalTypesRepository)
        repo.exists.return_value = True
        repo.list.return_value = []
        repo.update.return_value = expected_entity

        result = await self.case.execute(id=type_id, data=data)

        assert result == expected_entity
        repo.update.assert_awaited_once()
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_when_not_found(self) -> None:
        type_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_type_update()
        repo = self.uow.get_repository(IAnimalTypesRepository)
        repo.exists.return_value = False

        with pytest.raises(NotFoundError):
            await self.case.execute(id=type_id, data=data)

        repo.update.assert_not_called()
        self.uow.commit.assert_not_called()
