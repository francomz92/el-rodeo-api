"""Unit tests for animal use cases."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from tests.factories import (
    make_animal_create,
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
from src.cattle.application.uses_cases.animals_use_cases.register_animal_case import (
    RegisterAnimalCase,
)
from src.cattle.application.uses_cases.animals_use_cases.update_animal_case import (
    UpdateAnimalCase,
)
from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.events.animal_events import AnimalCreated
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.services.animal_protocols.create_animal_protocol_service import CreateAnimalProtocolService
from src.cattle.domain.services.animals.delete_animal_service import DeleteAnimalService
from src.cattle.domain.services.animals.get_animal_service import GetAnimalService
from src.cattle.domain.services.animals.list_animal_service import ListAnimalService
from src.cattle.domain.services.animals.register_animal_service import RegisterAnimalService
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
        expected_entity = make_animal_entity(id=animal_id)
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = expected_entity

        result = await self.case.execute(id=animal_id)

        assert result == expected_entity
        repo.get_by_id.assert_awaited_once_with(id=animal_id)

    async def test_execute_raises_when_not_found(self) -> None:
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.case.execute(
                id=UUID("00000000-0000-0000-0000-000000000001"),
            )


class TestListAnimalsCase:
    """ListAnimalsCase lists animals for a user."""

    def setup_method(self) -> None:
        self.service = ListAnimalService()
        self.uow = MockUoW()
        self.case = ListAnimalsCase(uow=self.uow, service=self.service)

    async def test_execute_returns_animal_list(self) -> None:
        expected_entities = [make_animal_entity(), make_animal_entity()]
        filters = make_animal_list_params()
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.list_for_user.return_value = (expected_entities, 2, False)

        items, total, next_cursor = await self.case.execute(
            filters=filters,
            limit=10,
            offset=0,
            order_by="name",
        )

        assert items == expected_entities
        assert total == 2
        assert next_cursor is None  # no cursor param → no next_cursor
        repo.list_for_user.assert_awaited_once_with(
            filters=filters,
            limit=10,
            offset=0,
            order_by="name",
            cursor=None,
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
        existing = make_animal_entity(id=animal_id)
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = existing

        await self.case.execute(id=animal_id)

        repo.delete.assert_awaited_once_with(id=animal_id)
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_when_not_found(self) -> None:
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.case.execute(
                id=UUID("00000000-0000-0000-0000-000000000001"),
            )

        repo.delete.assert_not_called()
        self.uow.commit.assert_not_called()

    async def test_execute_raises_when_sold(self) -> None:
        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        sold = make_animal_entity(id=animal_id, status=AnimalStatus.SOLD)
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.get_by_id.return_value = sold

        with pytest.raises(ConflictError):
            await self.case.execute(id=animal_id)

        repo.delete.assert_not_called()
        self.uow.commit.assert_not_called()


class TestRegisterAnimalCase:
    """RegisterAnimalCase registers a new animal and dispatches AnimalCreated."""

    def setup_method(self) -> None:
        self.service = MagicMock(spec=RegisterAnimalService)
        self.protocol_service = MagicMock(spec=CreateAnimalProtocolService)
        self.event_bus = AsyncMock()
        self.uow = MockUoW()
        self.case = RegisterAnimalCase(
            uow=self.uow,
            service=self.service,
            create_animal_protocol_service=self.protocol_service,
            event_bus=self.event_bus,
        )

    async def test_execute_creates_animal_and_dispatches_event(self) -> None:
        """Successful execution dispatches AnimalCreated after commit."""
        data = make_animal_create()
        animal = make_animal_entity()
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.create.return_value = animal
        type_repo = self.uow.get_repository(IAnimalTypesRepository)
        type_repo.exists.return_value = True
        self.service.create_new.return_value = animal

        result = await self.case.execute(data=data)

        assert result is animal
        self.service.validate_duplicate.assert_awaited_once()
        self.service.validate_type_exists.assert_awaited_once()
        self.service.create_new.assert_awaited_once_with(
            data=data,
            repository=repo,
        )
        self.protocol_service.create_new.assert_awaited_once()
        self.uow.commit.assert_awaited_once()

        # AnimalCreated event dispatched after commit
        self.event_bus.dispatch.assert_called_once()
        (dispatched_event,) = self.event_bus.dispatch.call_args[0]
        assert isinstance(dispatched_event, AnimalCreated)
        assert dispatched_event.aggregate_id == animal.id

    async def test_execute_dispatches_event_after_commit(self) -> None:
        """Event dispatch happens AFTER uow.commit, not before."""
        data = make_animal_create()
        animal = make_animal_entity()
        repo = self.uow.get_repository(IAnimalsRepository)
        repo.create.return_value = animal
        type_repo = self.uow.get_repository(IAnimalTypesRepository)
        type_repo.exists.return_value = True
        self.service.create_new.return_value = animal

        # Track execution order
        call_order: list[str] = []

        original_commit = self.uow.commit

        async def tracking_commit() -> None:
            call_order.append("commit")
            await original_commit()

        self.uow.commit = tracking_commit

        original_dispatch = self.event_bus.dispatch

        async def tracking_dispatch(event):
            call_order.append("dispatch")
            await original_dispatch(event)

        self.event_bus.dispatch = tracking_dispatch

        await self.case.execute(data=data)

        assert call_order == ["commit", "dispatch"]
