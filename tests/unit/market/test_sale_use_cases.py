"""Unit tests for sale use cases.

Use cases orchestrate domain services and repositories via the Unit of Work.
Here we mock the UoW to test the orchestration logic in isolation.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from tests.factories import (
    make_animal_entity,
    make_animal_protocol_entity,
    make_sale_create,
    make_sale_entity,
    make_sale_list_params,
    make_sale_update,
)
from tests.mocks import MockUoW

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.common.domain.exceptions import BusinessValidationError, NotFoundError
from src.market.application.uses_cases.sale_cases.create_sale_case import (
    CreateSaleCase,
)
from src.market.application.uses_cases.sale_cases.delete_sale_case import (
    DeleteSaleCase,
)
from src.market.application.uses_cases.sale_cases.get_sale_case import GetSaleCase
from src.market.application.uses_cases.sale_cases.list_sale_case import ListSaleCase
from src.market.application.uses_cases.sale_cases.update_sale_case import UpdateSaleCase
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.services.sale_services.create_sale_service import (
    CreateSaleService,
)
from src.market.domain.services.sale_services.delete_sale_service import (
    DeleteSaleService,
)
from src.market.domain.services.sale_services.get_sale_service import GetSaleService
from src.market.domain.services.sale_services.list_sale_service import ListSaleService
from src.market.domain.services.sale_services.update_sale_service import UpdateSaleService
from src.market.domain.value_objects.sale_value_objects import SaleCreateValueObject


class TestCreateSaleCase:
    """CreateSaleCase orchestrates validation + creation via UoW."""

    def setup_method(self) -> None:
        self.service = CreateSaleService()
        self.uow = MockUoW()
        self.case = CreateSaleCase(uow=self.uow, service=self.service)
        self.animal_id = UUID("00000000-0000-0000-0000-00000000000a")

    def _setup_eligibility_mocks(self, animal=None, protocol=None):
        """Set up animal and protocol repos for a successful eligibility check."""
        animal_repo = self.uow.get_repository(IAnimalsRepository)
        protocol_repo = self.uow.get_repository(IAnimalProtocolsRepository)
        animal_repo.get_by_id.return_value = animal
        protocol_repo.get_by_animal_id.return_value = protocol
        return animal_repo, protocol_repo

    def _make_eligible_protocol(self, animal):
        """Build an AnimalProtocolEntity with sale-permission granted."""
        from datetime import date

        from tests.factories import make_animal_protocol_entity

        return make_animal_protocol_entity(
            animal=animal,
            vaccinated=True,
            vaccinated_date=date.today(),
            sale_permission=True,
            sale_permission_date=date.today(),
        )

    async def test_execute_creates_sale_successfully(self) -> None:
        """Happy path: valid data → repository called → entity returned."""
        data = make_sale_create(
            animal_id=self.animal_id,
        )
        expected_entity = make_sale_entity()
        repo = self.uow.get_repository(ISalesRepository)
        repo.create.return_value = expected_entity

        # Set up eligibility mocks so the check passes
        animal = make_animal_entity(id=self.animal_id, status=AnimalStatus.READY)
        self._setup_eligibility_mocks(
            animal=animal,
            protocol=self._make_eligible_protocol(animal),
        )

        result = await self.case.execute(data)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(data)

    async def test_execute_calls_commit(self) -> None:
        """A successful creation commits the transaction."""
        data = make_sale_create(
            animal_id=self.animal_id,
        )
        repo = self.uow.get_repository(ISalesRepository)
        repo.create.return_value = make_sale_entity()

        # Set up eligibility mocks so the check passes
        animal = make_animal_entity(id=self.animal_id, status=AnimalStatus.READY)
        self._setup_eligibility_mocks(
            animal=animal,
            protocol=self._make_eligible_protocol(animal),
        )

        await self.case.execute(data)

        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_on_invalid_data(self) -> None:
        """Invalid data raises BusinessValidationError without calling the repo."""
        data = make_sale_create(
            price_per_kg=Decimal("5000"),
            price=Decimal("1000"),
            weight=1.0,
            animal_id=self.animal_id,
        )
        repo = self.uow.get_repository(ISalesRepository)

        with pytest.raises(BusinessValidationError):
            await self.case.execute(data)

        repo.create.assert_not_called()

    async def test_execute_updates_animal_status_to_sold(self) -> None:
        """After sale creation, animal status is updated to SOLD in the same UoW."""
        data = make_sale_create(
            animal_id=self.animal_id,
        )
        repo = self.uow.get_repository(ISalesRepository)
        animal_repo = self.uow.get_repository(IAnimalsRepository)
        repo.create.return_value = make_sale_entity()

        # Set up eligibility mocks so the check passes
        animal = make_animal_entity(id=self.animal_id, status=AnimalStatus.READY)
        self._setup_eligibility_mocks(
            animal=animal,
            protocol=self._make_eligible_protocol(animal),
        )

        await self.case.execute(data)

        # Animal status must be set to SOLD after sale creation
        animal_repo.update_status.assert_awaited_once_with(
            self.animal_id,
            AnimalStatus.SOLD,
        )
        # Sale was still created (committed)
        self.uow.commit.assert_awaited_once()


class TestCreateSaleServiceEligibility:
    """CreateSaleService.validate_eligibility — pre-sale eligibility checks."""

    def setup_method(self) -> None:
        self.service = CreateSaleService()
        self.animal_id = UUID("00000000-0000-0000-0000-00000000000a")

    async def _make_mocks(self, animal=None, protocol=None):
        """Helper: set up animal_repo and protocol_repo with given returns."""
        animal_repo = AsyncMock()
        protocol_repo = AsyncMock()
        animal_repo.get_by_id.return_value = animal
        protocol_repo.get_by_animal_id.return_value = protocol
        return animal_repo, protocol_repo

    async def test_eligible_animal_passes(self) -> None:
        """An animal with can_be_sold() == True passes eligibility."""
        from datetime import date

        animal = make_animal_entity(id=self.animal_id, status=AnimalStatus.READY)
        protocol = make_animal_protocol_entity(
            animal=animal,
            vaccinated=True,
            vaccinated_date=date.today(),
            sale_permission=True,
            sale_permission_date=date.today(),
        )
        animal_repo, protocol_repo = await self._make_mocks(animal, protocol)

        result = await self.service.validate_eligibility(
            self.animal_id,
            animal_repo,
            protocol_repo,
        )

        assert result is None
        animal_repo.get_by_id.assert_awaited_once_with(self.animal_id)
        protocol_repo.get_by_animal_id.assert_awaited_once_with(self.animal_id)

    async def test_raises_when_animal_not_found(self) -> None:
        """Raises NotFoundError when animal does not exist."""
        animal_repo, protocol_repo = await self._make_mocks(animal=None, protocol=None)

        with pytest.raises(NotFoundError):
            await self.service.validate_eligibility(
                self.animal_id,
                animal_repo,
                protocol_repo,
            )

    async def test_raises_when_no_protocol(self) -> None:
        """Raises BusinessValidationError when no protocol exists for the animal."""
        animal = make_animal_entity(id=self.animal_id)
        animal_repo, protocol_repo = await self._make_mocks(animal=animal, protocol=None)

        with pytest.raises(BusinessValidationError):
            await self.service.validate_eligibility(
                self.animal_id,
                animal_repo,
                protocol_repo,
            )

    async def test_raises_when_already_sold(self) -> None:
        """Raises BusinessValidationError when animal is already SOLD."""
        from datetime import date

        animal = make_animal_entity(id=self.animal_id, status=AnimalStatus.SOLD)
        protocol = make_animal_protocol_entity(
            animal=animal,
            vaccinated=True,
            vaccinated_date=date.today(),
            sale_permission=True,
            sale_permission_date=date.today(),
        )
        animal_repo, protocol_repo = await self._make_mocks(animal, protocol)

        with pytest.raises(BusinessValidationError):
            await self.service.validate_eligibility(
                self.animal_id,
                animal_repo,
                protocol_repo,
            )

    async def test_raises_when_unvaccinated(self) -> None:
        """Raises BusinessValidationError when animal is not vaccinated."""
        from datetime import date

        animal = make_animal_entity(id=self.animal_id, status=AnimalStatus.READY)
        protocol = make_animal_protocol_entity(
            animal=animal,
            vaccinated=False,
            sale_permission=True,
            sale_permission_date=date.today(),
        )
        animal_repo, protocol_repo = await self._make_mocks(animal, protocol)

        with pytest.raises(BusinessValidationError):
            await self.service.validate_eligibility(
                self.animal_id,
                animal_repo,
                protocol_repo,
            )

    async def test_raises_when_no_sale_permission(self) -> None:
        """Raises BusinessValidationError when animal lacks sale permission."""
        from datetime import date

        animal = make_animal_entity(id=self.animal_id, status=AnimalStatus.READY)
        protocol = make_animal_protocol_entity(
            animal=animal,
            vaccinated=True,
            vaccinated_date=date.today(),
            sale_permission=False,
        )
        animal_repo, protocol_repo = await self._make_mocks(animal, protocol)

        with pytest.raises(BusinessValidationError):
            await self.service.validate_eligibility(
                self.animal_id,
                animal_repo,
                protocol_repo,
            )


class TestCreateSaleServicePricePerKg:
    """CreateSaleService.validate_data — price_per_kg * weight vs price consistency."""

    def setup_method(self) -> None:
        self.service = CreateSaleService()

    async def test_consistent_price_passes(self) -> None:
        """price_per_kg * weight matching price passes validation."""
        data = SaleCreateValueObject(
            user_id=UUID("00000000-0000-0000-0000-000000000001"),
            animal_id=UUID("00000000-0000-0000-0000-000000000002"),
            buyer_id=UUID("00000000-0000-0000-0000-000000000003"),
            sale_date=date(2025, 1, 1),
            price=Decimal("600.0"),
            price_per_kg=Decimal("3.0"),
            weight=200.0,
        )

        # validate_data runs synchronously, no await needed
        self.service.validate_data(data)

    async def test_slightly_off_but_within_tolerance_passes(self) -> None:
        """price_per_kg * weight within 10% tolerance passes."""
        # 3.0 * 200 = 600, |600-650|/650 = 0.077 < 0.1 → passes
        data = SaleCreateValueObject(
            user_id=UUID("00000000-0000-0000-0000-000000000001"),
            animal_id=UUID("00000000-0000-0000-0000-000000000002"),
            buyer_id=UUID("00000000-0000-0000-0000-000000000003"),
            sale_date=date(2025, 1, 1),
            price=Decimal("650.0"),
            price_per_kg=Decimal("3.0"),
            weight=200.0,
        )

        self.service.validate_data(data)

    async def test_inconsistent_price_raises_error(self) -> None:
        """price_per_kg * weight off by >10% raises BusinessValidationError."""
        # 3.0 * 200 = 600, |600-500|/500 = 0.2 > 0.1 → should raise
        data = SaleCreateValueObject(
            user_id=UUID("00000000-0000-0000-0000-000000000001"),
            animal_id=UUID("00000000-0000-0000-0000-000000000002"),
            buyer_id=UUID("00000000-0000-0000-0000-000000000003"),
            sale_date=date(2025, 1, 1),
            price=Decimal("500.0"),
            price_per_kg=Decimal("3.0"),
            weight=200.0,
        )

        with pytest.raises(BusinessValidationError):
            self.service.validate_data(data)

    async def test_dead_code_removed(self) -> None:
        """SaleEntity.validate_price_per_kg no longer exists."""
        from src.market.domain.entities.sales import SaleEntity

        assert not hasattr(SaleEntity, "validate_price_per_kg")


class TestGetSaleCase:
    """GetSaleCase retrieves a single sale."""

    def setup_method(self) -> None:
        self.service = GetSaleService()
        self.uow = MockUoW()
        self.case = GetSaleCase(uow=self.uow, service=self.service)

    async def test_execute_returns_sale(self) -> None:
        """get_by_id is called and the entity is returned."""
        sale_id = UUID("00000000-0000-0000-0000-000000000001")
        expected_entity = make_sale_entity(id=sale_id)
        repo = self.uow.get_repository(ISalesRepository)
        repo.get_by_id.return_value = expected_entity

        result = await self.case.execute(id=sale_id)

        assert result == expected_entity
        repo.get_by_id.assert_awaited_once_with(sale_id)

    async def test_execute_raises_when_not_found(self) -> None:
        """Raises NotFoundError if the sale does not exist."""
        repo = self.uow.get_repository(ISalesRepository)
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.case.execute(
                id=UUID("00000000-0000-0000-0000-000000000001"),
            )


class TestListSaleCase:
    """ListSaleCase lists sales for a user with filters."""

    def setup_method(self) -> None:
        self.service = ListSaleService()
        self.uow = MockUoW()
        self.case = ListSaleCase(uow=self.uow, service=self.service)

    async def test_execute_returns_sale_list(self) -> None:
        """list_for_user is called with the correct parameters."""
        expected_entities = [make_sale_entity(), make_sale_entity()]
        params = make_sale_list_params()
        repo = self.uow.get_repository(ISalesRepository)
        repo.list_for_user.return_value = expected_entities

        result = await self.case.execute(
            filters=params,
            limit=10,
            offset=0,
            order_by="created_at",
        )

        assert result == expected_entities
        repo.list_for_user.assert_awaited_once_with(
            filters=params,
            limit=10,
            offset=0,
            order_by="created_at",
            user_id=None,
        )


class TestDeleteSaleCase:
    """DeleteSaleCase deletes a sale after verifying ownership."""

    def setup_method(self) -> None:
        self.service = DeleteSaleService()
        self.uow = MockUoW()
        self.case = DeleteSaleCase(uow=self.uow, service=self.service)

    async def test_execute_deletes_sale(self) -> None:
        """Deletes when the sale exists."""
        sale_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = self.uow.get_repository(ISalesRepository)
        repo.delete.return_value = True

        await self.case.execute(id=sale_id)

        repo.delete.assert_awaited_once_with(sale_id)

    async def test_execute_raises_when_not_found(self) -> None:
        """Raises when the sale does not exist for this user."""
        sale_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = self.uow.get_repository(ISalesRepository)
        repo.delete.return_value = False

        with pytest.raises(NotFoundError):
            await self.case.execute(id=sale_id)

        repo.delete.assert_awaited_once_with(sale_id)


class TestUpdateSaleCase:
    """UpdateSaleCase updates a sale after verifying ownership."""

    def setup_method(self) -> None:
        self.service = UpdateSaleService()
        self.uow = MockUoW()
        self.case = UpdateSaleCase(uow=self.uow, service=self.service)

    async def test_execute_updates_sale_successfully(self) -> None:
        """Updates + commits when the sale exists."""
        sale_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_sale_update(price=Decimal("2500"))
        expected_entity = make_sale_entity(id=sale_id, price=Decimal("2500"))
        repo = self.uow.get_repository(ISalesRepository)
        repo.update_data.return_value = expected_entity

        result = await self.case.execute(id=sale_id, data=data)

        assert result == expected_entity
        repo.update_data.assert_awaited_once_with(sale_id, data)
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_when_not_found(self) -> None:
        """Raises NotFoundError when update_data returns None."""
        sale_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_sale_update(price=Decimal("2500"))
        repo = self.uow.get_repository(ISalesRepository)
        repo.update_data.return_value = None

        with pytest.raises(NotFoundError):
            await self.case.execute(id=sale_id, data=data)

        repo.update_data.assert_awaited_once_with(sale_id, data)
        self.uow.commit.assert_not_called()
