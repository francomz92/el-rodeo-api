"""Unit tests for animal supply use cases."""

from uuid import UUID

from tests.factories import (
    make_animal_supply_create,
    make_animal_supply_entity,
    make_animal_supply_list_params,
    make_animal_supply_update,
)
from tests.mocks import MockUoW

from src.finance.application.uses_cases.animal_supplies_cases.create_animal_supplies_cases import (
    CreateAnimalSuppliesCase,
)
from src.finance.application.uses_cases.animal_supplies_cases.delete_animal_supplies_case import (
    DeleteAnimalSuppliesCase,
)
from src.finance.application.uses_cases.animal_supplies_cases.get_animal_supplies_cases import (
    GetAnimalSuppliesCase,
)
from src.finance.application.uses_cases.animal_supplies_cases.list_animal_supplies_case import (
    ListAnimalSuppliesCase,
)
from src.finance.application.uses_cases.animal_supplies_cases.update_animal_supplies_case import (
    UpdateAnimalSuppliesCase,
)
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.repositories.animal_supply_types import ISupplyTypesRepository
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
from src.finance.domain.services.animal_supply_type_services.get_animal_supply_type_service import (
    GetSupplyTypeService,
)


class TestCreateAnimalSuppliesCase:
    """CreateAnimalSuppliesCase creates a supply via UoW."""

    def setup_method(self) -> None:
        self.service = CreateAnimalSuppliesService()
        self.get_supply_type_service = GetSupplyTypeService()
        self.uow = MockUoW()
        self.case = CreateAnimalSuppliesCase(
            uow=self.uow,
            service=self.service,
            get_supply_type_service=self.get_supply_type_service,
        )

    async def test_execute_creates_supply_successfully(self) -> None:
        data = make_animal_supply_create(amount=100.0, critical_amount=20.0)
        expected = make_animal_supply_entity()
        repo = self.uow.get_repository(IAnimalSuppliesRepository)
        type_repo = self.uow.get_repository(ISupplyTypesRepository)
        repo.create.return_value = expected
        type_repo.exists.return_value = True

        result = await self.case.execute(data)

        assert result == expected
        repo.create.assert_awaited_once_with(data)
        self.uow.commit.assert_awaited_once()


class TestGetAnimalSuppliesCase:
    """GetAnimalSuppliesCase retrieves a supply."""

    def setup_method(self) -> None:
        self.service = GetAnimalSuppliesService()
        self.uow = MockUoW()
        self.case = GetAnimalSuppliesCase(uow=self.uow, service=self.service)

    async def test_execute_returns_supply(self) -> None:
        supply_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        expected = make_animal_supply_entity(id=supply_id)
        repo = self.uow.get_repository(IAnimalSuppliesRepository)
        repo.get_by_id.return_value = expected

        result = await self.case.execute(id=supply_id, user_id=user_id)

        assert result == expected


class TestListAnimalSuppliesCase:
    """ListAnimalSuppliesCase lists supplies."""

    def setup_method(self) -> None:
        self.service = ListAnimalSuppliesService()
        self.uow = MockUoW()
        self.case = ListAnimalSuppliesCase(uow=self.uow, service=self.service)

    async def test_execute_returns_list(self) -> None:
        user_id = UUID("00000000-0000-0000-0000-000000000001")
        filters = make_animal_supply_list_params()
        expected = [make_animal_supply_entity(), make_animal_supply_entity()]
        repo = self.uow.get_repository(IAnimalSuppliesRepository)
        repo.list_for_user.return_value = expected

        result = await self.case.execute(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="name",
        )

        assert result == expected


class TestUpdateAnimalSuppliesCase:
    """UpdateAnimalSuppliesCase updates a supply."""

    def setup_method(self) -> None:
        self.service = UpdateAnimalSuppliesService()
        self.get_supply_type_service = GetSupplyTypeService()
        self.uow = MockUoW()
        self.case = UpdateAnimalSuppliesCase(
            uow=self.uow,
            service=self.service,
            get_supply_type_service=self.get_supply_type_service,
        )

    async def test_execute_updates_successfully(self) -> None:
        supply_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_supply_update(amount=100.0, critical_amount=20.0)
        expected = make_animal_supply_entity(id=supply_id)
        repo = self.uow.get_repository(IAnimalSuppliesRepository)
        repo.update_data.return_value = expected

        result = await self.case.execute(id=supply_id, user_id=UUID("00000000-0000-0000-0000-000000000002"), data=data)

        assert result == expected
        repo.update_data.assert_awaited_once()
        self.uow.commit.assert_awaited_once()


class TestDeleteAnimalSuppliesCase:
    """DeleteAnimalSuppliesCase deletes a supply."""

    def setup_method(self) -> None:
        self.service = DeleteAnimalSuppliesService()
        self.uow = MockUoW()
        self.case = DeleteAnimalSuppliesCase(uow=self.uow, service=self.service)

    async def test_execute_deletes_supply(self) -> None:
        supply_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        repo = self.uow.get_repository(IAnimalSuppliesRepository)
        repo.exists.return_value = True

        await self.case.execute(id=supply_id, user_id=user_id)

        repo.delete.assert_awaited_once_with(supply_id)
        self.uow.commit.assert_awaited_once()
