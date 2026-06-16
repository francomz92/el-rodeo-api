"""Unit tests for animal supply type use cases."""

from uuid import UUID

import pytest
from tests.factories import (
    make_supply_type_create,
    make_supply_type_entity,
    make_supply_type_list_params,
    make_supply_type_update,
)
from tests.mocks import MockUoW

from src.common.domain.exceptions import ConflictError, NotFoundError
from src.finance.application.uses_cases.animal_supply_type_cases.create_animal_supply_type_case import (
    CreateAnimalSupplyTypeCase,
)
from src.finance.application.uses_cases.animal_supply_type_cases.delete_animal_supply_type_case import (
    DeleteAnimalSupplyTypeCase,
)
from src.finance.application.uses_cases.animal_supply_type_cases.list_animal_supply_type_case import (
    ListAnimalSupplyTypeCase,
)
from src.finance.application.uses_cases.animal_supply_type_cases.update_animal_supply_type_case import (
    UpdateAnimalSupplyTypeCase,
)
from src.finance.domain.repositories.animal_supply_types import ISupplyTypesRepository
from src.finance.domain.services.animal_supply_type_services.create_animal_supply_type_service import (
    CreateAnimalSupplyTypeService,
)
from src.finance.domain.services.animal_supply_type_services.delete_animal_supply_type_service import (
    DeleteAnimalSupplyTypeService,
)
from src.finance.domain.services.animal_supply_type_services.list_animal_supply_type_service import (
    ListAnimalSupplyTypeService,
)
from src.finance.domain.services.animal_supply_type_services.update_animal_supply_type_service import (
    UpdateAnimalSupplyTypeService,
)


class TestCreateAnimalSupplyTypeCase:
    """CreateAnimalSupplyTypeCase creates a supply type via UoW."""

    def setup_method(self) -> None:
        self.service = CreateAnimalSupplyTypeService()
        self.uow = MockUoW()
        self.case = CreateAnimalSupplyTypeCase(uow=self.uow, service=self.service)

    async def test_execute_creates_successfully(self) -> None:
        data = make_supply_type_create()
        expected = make_supply_type_entity()
        repo = self.uow.get_repository(ISupplyTypesRepository)
        repo.get_by_name.return_value = None
        repo.create.return_value = expected

        result = await self.case.execute(data)

        assert result == expected
        repo.create.assert_awaited_once_with(data)
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_on_duplicate(self) -> None:
        data = make_supply_type_create()
        repo = self.uow.get_repository(ISupplyTypesRepository)
        repo.get_by_name.return_value = make_supply_type_entity()

        with pytest.raises(ConflictError):
            await self.case.execute(data)

        repo.create.assert_not_called()
        self.uow.commit.assert_not_called()


class TestListAnimalSupplyTypeCase:
    """ListAnimalSupplyTypeCase lists supply types."""

    def setup_method(self) -> None:
        self.service = ListAnimalSupplyTypeService()
        self.uow = MockUoW()
        self.case = ListAnimalSupplyTypeCase(uow=self.uow, service=self.service)

    async def test_execute_returns_list(self) -> None:
        expected = [make_supply_type_entity(), make_supply_type_entity()]
        filters = make_supply_type_list_params()
        repo = self.uow.get_repository(ISupplyTypesRepository)
        repo.list.return_value = expected

        result = await self.case.execute(filters=filters, limit=10, offset=0, order_by="name")

        assert result == expected


class TestUpdateAnimalSupplyTypeCase:
    """UpdateAnimalSupplyTypeCase updates a supply type."""

    def setup_method(self) -> None:
        self.service = UpdateAnimalSupplyTypeService()
        self.uow = MockUoW()
        self.case = UpdateAnimalSupplyTypeCase(uow=self.uow, service=self.service)

    async def test_execute_updates_successfully(self) -> None:
        type_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_supply_type_update()
        expected = make_supply_type_entity(id=type_id)
        repo = self.uow.get_repository(ISupplyTypesRepository)
        repo.get_by_id.return_value = make_supply_type_entity(id=type_id)
        repo.get_by_name.return_value = None
        repo.update.return_value = expected

        await self.case.execute(id=type_id, data=data)

        repo.update.assert_awaited_once()
        self.uow.commit.assert_awaited_once()


class TestDeleteAnimalSupplyTypeCase:
    """DeleteAnimalSupplyTypeCase deletes a supply type."""

    def setup_method(self) -> None:
        self.service = DeleteAnimalSupplyTypeService()
        self.uow = MockUoW()
        self.case = DeleteAnimalSupplyTypeCase(uow=self.uow, service=self.service)

    async def test_execute_deletes_successfully(self) -> None:
        type_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = self.uow.get_repository(ISupplyTypesRepository)
        repo.exists.return_value = True

        await self.case.execute(id=type_id)

        repo.delete.assert_awaited_once_with(type_id)
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_when_not_found(self) -> None:
        type_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = self.uow.get_repository(ISupplyTypesRepository)
        repo.exists.return_value = False

        with pytest.raises(NotFoundError):
            await self.case.execute(id=type_id)

        repo.delete.assert_not_called()
        self.uow.commit.assert_not_called()
