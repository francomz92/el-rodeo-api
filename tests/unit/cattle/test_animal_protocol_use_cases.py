"""Unit tests for animal protocol use cases."""

from uuid import UUID

import pytest
from tests.factories import (
    make_animal_protocol_entity,
    make_animal_protocol_list_params,
    make_animal_protocol_update,
)
from tests.mocks import MockUoW

from src.cattle.application.uses_cases.animal_protocols_cases.delete_animal_protocol_case import (
    DeleteAnimalProtocolCase,
)
from src.cattle.application.uses_cases.animal_protocols_cases.get_animal_protocol_case import (
    GetAnimalProtocolCase,
)
from src.cattle.application.uses_cases.animal_protocols_cases.list_animal_protocols_case import (
    ListAnimalProtocolsCase,
)
from src.cattle.application.uses_cases.animal_protocols_cases.update_animal_protocols_case import (
    UpdateAnimalProtocolsCase,
)
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.services.animal_protocols.delete_animal_protocol_service import (
    DeleteAnimalProtocolService,
)
from src.cattle.domain.services.animal_protocols.get_animal_protocol_service import (
    GetAnimalProtocolService,
)
from src.cattle.domain.services.animal_protocols.list_animal_protocol_service import (
    ListAnimalProtocolService,
)
from src.cattle.domain.services.animal_protocols.update_animal_protocol_service import (
    UpdateAnimalProtocolService,
)
from src.common.domain.exceptions import NotFoundError


class TestGetAnimalProtocolCase:
    """GetAnimalProtocolCase retrieves a protocol."""

    def setup_method(self) -> None:
        self.service = GetAnimalProtocolService()
        self.uow = MockUoW()
        self.case = GetAnimalProtocolCase(uow=self.uow, service=self.service)

    async def test_execute_returns_protocol(self) -> None:
        protocol_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        expected = make_animal_protocol_entity(id=protocol_id)
        repo = self.uow.get_repository(IAnimalProtocolsRepository)
        repo.get_by_id.return_value = expected

        result = await self.case.execute(protocol_id, user_id)

        assert result == expected
        repo.get_by_id.assert_awaited_once_with(protocol_id, user_id)

    async def test_execute_raises_when_not_found(self) -> None:
        repo = self.uow.get_repository(IAnimalProtocolsRepository)
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.case.execute(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
            )


class TestListAnimalProtocolsCase:
    """ListAnimalProtocolsCase lists protocols."""

    def setup_method(self) -> None:
        self.service = ListAnimalProtocolService()
        self.uow = MockUoW()
        self.case = ListAnimalProtocolsCase(uow=self.uow, service=self.service)

    async def test_execute_returns_protocol_list(self) -> None:
        user_id = UUID("00000000-0000-0000-0000-000000000001")
        expected = [make_animal_protocol_entity(), make_animal_protocol_entity()]
        filters = make_animal_protocol_list_params()
        repo = self.uow.get_repository(IAnimalProtocolsRepository)
        repo.list_for_user.return_value = expected

        result = await self.case.execute(user_id, filters, limit=10, offset=0, order_by="id")

        assert result == expected
        repo.list_for_user.assert_awaited_once_with(user_id, filters, limit=10, offset=0, order_by="id")


class TestUpdateAnimalProtocolsCase:
    """UpdateAnimalProtocolsCase updates a protocol."""

    def setup_method(self) -> None:
        self.service = UpdateAnimalProtocolService()
        self.uow = MockUoW()
        self.case = UpdateAnimalProtocolsCase(uow=self.uow, service=self.service)

    async def test_execute_updates_successfully(self) -> None:
        protocol_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_protocol_update(vaccinated=False, sale_permission=False)
        expected = make_animal_protocol_entity(id=protocol_id)
        repo = self.uow.get_repository(IAnimalProtocolsRepository)
        repo.get_by_id.return_value = make_animal_protocol_entity(id=protocol_id)
        repo.update_data.return_value = expected

        result = await self.case.execute(protocol_id, data)

        assert result == expected
        repo.update_data.assert_awaited_once()
        self.uow.commit.assert_awaited_once()


class TestDeleteAnimalProtocolCase:
    """DeleteAnimalProtocolCase deletes a protocol."""

    def setup_method(self) -> None:
        self.service = DeleteAnimalProtocolService()
        self.uow = MockUoW()
        self.case = DeleteAnimalProtocolCase(uow=self.uow, service=self.service)

    async def test_execute_deletes_protocol(self) -> None:
        protocol_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        repo = self.uow.get_repository(IAnimalProtocolsRepository)
        repo.get_by_id.return_value = make_animal_protocol_entity(id=protocol_id)

        await self.case.execute(protocol_id, user_id)

        repo.delete.assert_awaited_once_with(protocol_id)
        self.uow.commit.assert_awaited_once()
