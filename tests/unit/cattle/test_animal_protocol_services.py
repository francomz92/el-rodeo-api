"""Unit tests for animal protocol domain services."""

from uuid import UUID

import pytest
from tests.factories import (
    make_animal_entity,
    make_animal_protocol_create,
    make_animal_protocol_entity,
    make_animal_protocol_list_params,
    make_animal_protocol_update,
)

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.services.animal_protocols.create_animal_protocol_service import (
    CreateAnimalProtocolService,
)
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
from src.common.domain.exceptions import ConflictError, NotFoundError


class TestCreateAnimalProtocolService:
    """CreateAnimalProtocolService creates new animal protocols."""

    def setup_method(self) -> None:
        self.service = CreateAnimalProtocolService()

    async def test_create_new_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        user_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_protocol_create()
        expected_entity = make_animal_protocol_entity()
        repo = AsyncMock()
        repo.create.return_value = expected_entity

        result = await self.service.create_new(user_id, data, repo)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(user_id=user_id, data=data)


class TestGetAnimalProtocolService:
    """GetAnimalProtocolService retrieves a protocol."""

    def setup_method(self) -> None:
        self.service = GetAnimalProtocolService()

    async def test_get_animal_protocol_returns_entity(self) -> None:
        from unittest.mock import AsyncMock

        protocol_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        expected_entity = make_animal_protocol_entity(id=protocol_id)
        repo = AsyncMock()
        repo.get_by_id.return_value = expected_entity

        result = await self.service.get_animal_protocol(protocol_id, user_id, repo)

        assert result == expected_entity
        repo.get_by_id.assert_awaited_once_with(protocol_id, user_id)

    async def test_get_animal_protocol_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.get_animal_protocol(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )


class TestListAnimalProtocolService:
    """ListAnimalProtocolService lists protocols."""

    def setup_method(self) -> None:
        self.service = ListAnimalProtocolService()

    async def test_get_animal_protocols_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        user_id = UUID("00000000-0000-0000-0000-000000000001")
        filters = make_animal_protocol_list_params()
        expected = [make_animal_protocol_entity(), make_animal_protocol_entity()]
        repo = AsyncMock()
        repo.list_for_user.return_value = expected

        result = await self.service.get_animal_protocols(
            user_id,
            repo,
            filters,
            limit=10,
            offset=0,
            order_by="id",
        )

        assert result == expected
        repo.list_for_user.assert_awaited_once_with(
            user_id,
            filters,
            limit=10,
            offset=0,
            order_by="id",
        )


class TestUpdateAnimalProtocolService:
    """UpdateAnimalProtocolService updates a protocol."""

    def setup_method(self) -> None:
        self.service = UpdateAnimalProtocolService()

    async def test_run_validations_passes(self) -> None:
        from unittest.mock import AsyncMock

        protocol_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_protocol_update(vaccinated=False, sale_permission=False)
        protocol = make_animal_protocol_entity(id=protocol_id)
        repo = AsyncMock()
        repo.get_by_id.return_value = protocol

        await self.service.run_validations(protocol_id, data, repo)

    async def test_run_validations_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None
        data = make_animal_protocol_update()

        with pytest.raises(NotFoundError):
            await self.service.run_validations(
                UUID("00000000-0000-0000-0000-000000000001"),
                data,
                repo,
            )

    async def test_run_validations_raises_when_sold(self) -> None:
        from unittest.mock import AsyncMock

        sold_animal = make_animal_entity(status=AnimalStatus.SOLD)
        protocol = make_animal_protocol_entity(animal=sold_animal)
        repo = AsyncMock()
        repo.get_by_id.return_value = protocol
        data = make_animal_protocol_update()

        with pytest.raises(ConflictError):
            await self.service.run_validations(
                UUID("00000000-0000-0000-0000-000000000001"),
                data,
                repo,
            )

    async def test_update_protocols_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        protocol_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_animal_protocol_update()
        expected_entity = make_animal_protocol_entity(id=protocol_id)
        repo = AsyncMock()
        repo.update_data.return_value = expected_entity

        result = await self.service.update_protocols(protocol_id, data, repo)

        assert result == expected_entity
        repo.update_data.assert_awaited_once_with(protocol_id, data)


class TestDeleteAnimalProtocolService:
    """DeleteAnimalProtocolService deletes a protocol."""

    def setup_method(self) -> None:
        self.service = DeleteAnimalProtocolService()

    async def test_validate_can_delete_passes(self) -> None:
        from unittest.mock import AsyncMock

        protocol = make_animal_protocol_entity()
        repo = AsyncMock()
        repo.get_by_id.return_value = protocol

        await self.service.validate_can_delete(
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            repo,
        )

    async def test_validate_can_delete_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.validate_can_delete(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )

    async def test_validate_can_delete_raises_when_sold(self) -> None:
        from unittest.mock import AsyncMock

        sold_animal = make_animal_entity(status=AnimalStatus.SOLD)
        protocol = make_animal_protocol_entity(animal=sold_animal)
        repo = AsyncMock()
        repo.get_by_id.return_value = protocol

        with pytest.raises(ConflictError):
            await self.service.validate_can_delete(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )

    async def test_delete_protocol_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        protocol_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = AsyncMock()

        await self.service.delete_protocol(protocol_id, repo)

        repo.delete.assert_awaited_once_with(protocol_id)
