"""Tests for repository instrumentation — audit calls from CUD methods.

Covers PR 2 tasks: 2.6–2.13 (instrumentation of 8 repositories).

Every test verifies that the repository's create/update/delete methods call
the mixin's _audit_create / _audit_update / _audit_delete with correct params.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.finance.domain.constants.animal_supplies import UnitOfMeasurement

# ── Helpers ─────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_session() -> AsyncMock:
    """Returns an AsyncMock with execute returning a basic mock result."""
    session = AsyncMock()

    default_result = MagicMock()
    default_result.scalar_one.return_value = uuid4()
    default_result.mappings.one_or_none.return_value = None
    default_result.mappings.all.return_value = []
    session.execute.return_value = default_result

    return session


@pytest.fixture
def tenant_id() -> UUID:
    return uuid4()


def make_row_dict(values: dict) -> MagicMock:
    """Create a MagicMock that behaves like RowMapping (dict-iterable)."""
    m = MagicMock()
    m.__iter__.side_effect = lambda: iter(values.items())
    return m


def make_old_row(values: dict) -> MagicMock:
    """Create a MagicMock that mimics execute().mappings().one_or_none()."""
    row_mock = MagicMock()
    row_mock.mappings.one_or_none.return_value = make_row_dict(values)
    return row_mock


def make_entity_mock(entity_id: UUID | None = None, **attrs) -> MagicMock:
    """Create a simple entity-like MagicMock with an id attribute."""
    m = MagicMock()
    m.id = entity_id or uuid4()
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


# ── 2.6 ScheduleEventRepository ─────────────────────────────────────────────


class TestScheduleEventRepositoryAudit:
    """Task 2.6: ScheduleEventRepository should call audit on CUD."""

    @pytest.fixture
    def repo(self, mock_session, tenant_id):
        from src.cattle.infrastructure.persistence.repositories.schedule_event_repository import (
            ScheduleEventRepository,
        )

        repo = ScheduleEventRepository(mock_session, tenant_id)
        repo.audit_repository = MagicMock()
        return repo

    @pytest.mark.asyncio
    async def test_create_calls_audit_create(self, repo, mock_session):
        """create() should call _audit_create after INSERT."""
        from src.cattle.domain.value_objects.schedule_event_value_object import (
            ScheduleEventCreationValueObject,
        )

        event_id = uuid4()
        mock_session.execute.return_value.scalar_one.return_value = event_id

        data = ScheduleEventCreationValueObject(
            user_id=uuid4(),
            title="Test Event",
            description="Desc",
            event_date="2026-07-01",
        )
        await repo.create(data)

        repo.audit_repository.record.assert_called_once()
        call_kwargs = repo.audit_repository.record.call_args[1]
        assert call_kwargs["action"] == "create"
        assert call_kwargs["entity_type"] == "schedule_event"
        assert call_kwargs["entity_id"] == event_id

    @pytest.mark.asyncio
    async def test_update_data_calls_audit_update(self, repo, mock_session):
        """update_data() should call _audit_update after UPDATE."""
        from src.cattle.domain.value_objects.schedule_event_value_object import (
            ScheduleEventUpdateValueObject,
        )

        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "title": "Old Title",
            }
        )

        data = ScheduleEventUpdateValueObject(user_id=uuid4(), title="New Title")

        await repo.update_data(entity_id, data)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "update"

    @pytest.mark.asyncio
    async def test_delete_calls_audit_delete(self, repo, mock_session):
        """delete() should call _audit_delete after DELETE."""
        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "title": "To Delete",
            }
        )

        await repo.delete(entity_id)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "delete"


# ── 2.7 AnimalSuppliesRepository ─────────────────────────────────────────────


class TestAnimalSuppliesRepositoryAudit:
    """Task 2.7: AnimalSuppliesRepository should call audit on CUD."""

    @pytest.fixture
    def repo(self, mock_session, tenant_id):
        from src.finance.infrastructure.persistence.repositories.animal_supplies import (
            AnimalSuppliesRepository,
        )

        repo = AnimalSuppliesRepository(mock_session, tenant_id)
        repo.audit_repository = MagicMock()
        # Stub get_by_id to avoid internal DB mock complexity
        repo.get_by_id = AsyncMock()
        repo.get_by_id.return_value = make_entity_mock()
        return repo

    @pytest.mark.asyncio
    async def test_create_calls_audit_create(self, repo, mock_session):
        """create() should call _audit_create after INSERT."""
        supply_id = uuid4()
        mock_session.execute.return_value.scalar_one.return_value = supply_id

        from src.finance.domain.value_objects.animal_supplies_value_objects import (
            AnimalSuppliesCreateValueObject,
        )

        data = AnimalSuppliesCreateValueObject(
            type_id=uuid4(),
            user_id=uuid4(),
            name="Test Supply",
            amount=10.0,
            critical_amount=2.0,
            unit_of_measurement=UnitOfMeasurement.UNIT,
            description="Test",
        )

        await repo.create(data)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "create"
        assert repo.audit_repository.record.call_args[1]["entity_type"] == "animal_supply"

    @pytest.mark.asyncio
    async def test_update_data_calls_audit_update(self, repo, mock_session):
        """update_data() should call _audit_update after UPDATE."""
        entity_id = uuid4()

        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "name": "Old Supply",
            }
        )

        from src.finance.domain.value_objects.animal_supplies_value_objects import (
            AnimalSuppliesUpdateValueObject,
        )

        data = AnimalSuppliesUpdateValueObject(
            type_id=uuid4(),
            name="New Supply",
            amount=20.0,
            critical_amount=3.0,
            unit_of_measurement=UnitOfMeasurement.UNIT,
            description="Updated",
        )

        await repo.update_data(entity_id, data)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "update"

    @pytest.mark.asyncio
    async def test_delete_calls_audit_delete(self, repo, mock_session):
        """delete() should call _audit_delete after DELETE."""
        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "name": "To Delete",
            }
        )

        await repo.delete(entity_id)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "delete"


# ── 2.8 PurchasesRepository ────────────────────────────────────────────────


class TestPurchasesRepositoryAudit:
    """Task 2.8: PurchasesRepository should call audit on CUD."""

    @pytest.fixture
    def repo(self, mock_session, tenant_id):
        from src.finance.infrastructure.persistence.repositories.purchases import (
            PurchasesRepository,
        )

        repo = PurchasesRepository(mock_session, tenant_id)
        repo.audit_repository = MagicMock()
        repo.get_by_id = AsyncMock()
        repo.get_by_id.return_value = make_entity_mock()
        return repo

    @pytest.mark.asyncio
    async def test_create_calls_audit_create(self, repo, mock_session):
        """create() should call _audit_create after INSERT."""
        purchase_id = uuid4()
        mock_session.execute.return_value.scalar_one.return_value = purchase_id

        from src.finance.domain.value_objects.purchase_value_objects import (
            PurchaseCreateValueObject,
        )

        data = PurchaseCreateValueObject(
            user_id=uuid4(),
            supply_id=uuid4(),
            amount=10.0,
            price=100.0,
            purchase_date="2026-07-01",
            unit_price=10.0,
            unit_of_measurement=UnitOfMeasurement.UNIT,
        )

        await repo.create(uuid4(), data)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "create"
        assert repo.audit_repository.record.call_args[1]["entity_type"] == "purchase"

    @pytest.mark.asyncio
    async def test_update_data_calls_audit_update(self, repo, mock_session):
        """update_data() should call _audit_update after UPDATE."""
        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "amount": 5.0,
                "price": 50.0,
            }
        )

        await repo.update_data(
            entity_id,
            amount=10.0,
            price=100.0,
            purchase_date="2026-07-01",
            unit_price=10.0,
            unit_of_measurement=UnitOfMeasurement.UNIT,
        )

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "update"

    @pytest.mark.asyncio
    async def test_delete_calls_audit_delete(self, repo, mock_session):
        """delete() should call _audit_delete after DELETE."""
        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "amount": 5.0,
            }
        )

        await repo.delete(entity_id)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "delete"


# ── 2.9 BuyersRepository ────────────────────────────────────────────────────


class TestBuyersRepositoryAudit:
    """Task 2.9: BuyersRepository should call audit on CUD."""

    @pytest.fixture
    def repo(self, mock_session, tenant_id):
        from src.market.infrastructure.persistence.repositories.buyers import (
            BuyersRepository,
        )

        repo = BuyersRepository(mock_session, tenant_id)
        repo.audit_repository = MagicMock()
        repo.get_by_id = AsyncMock()
        repo.get_by_id.return_value = make_entity_mock()
        return repo

    @pytest.mark.asyncio
    async def test_create_calls_audit_create(self, repo, mock_session):
        """create() should call _audit_create after INSERT."""
        buyer_id = uuid4()
        mock_session.execute.return_value.scalar_one.return_value = buyer_id

        from src.market.domain.value_objects.buyer_value_objects import (
            BuyerCreateValueObject,
        )

        data = BuyerCreateValueObject(
            user_id=uuid4(),
            name="Test Buyer",
            description="Test",
            contact_number="123456",
            contact_address="Addr",
        )

        await repo.create(data)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "create"
        assert repo.audit_repository.record.call_args[1]["entity_type"] == "buyer"

    @pytest.mark.asyncio
    async def test_update_data_calls_audit_update(self, repo, mock_session):
        """update_data() should call _audit_update after UPDATE."""
        entity_id = uuid4()
        first_call = make_old_row({"id": entity_id, "name": "Old Buyer"})
        second_call = MagicMock()
        second_call.scalar_one.return_value = entity_id
        mock_session.execute.side_effect = [first_call, second_call]

        from src.market.domain.value_objects.buyer_value_objects import (
            BuyerUpdateValueObject,
        )

        data = BuyerUpdateValueObject(name="New Buyer")
        await repo.update_data(entity_id, data)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "update"

    @pytest.mark.asyncio
    async def test_delete_calls_audit_delete(self, repo, mock_session):
        """delete() should call _audit_delete after DELETE."""
        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "name": "To Delete",
            }
        )

        await repo.delete(entity_id)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "delete"


# ── 2.10 SalesRepository ────────────────────────────────────────────────────


class TestSalesRepositoryAudit:
    """Task 2.10: SalesRepository should call audit on CUD."""

    @pytest.fixture
    def repo(self, mock_session, tenant_id):
        from src.market.infrastructure.persistence.repositories.sales import (
            SalesRepository,
        )

        repo = SalesRepository(mock_session, tenant_id)
        repo.audit_repository = MagicMock()
        repo.get_by_id = AsyncMock()
        repo.get_by_id.return_value = make_entity_mock()
        return repo

    @pytest.mark.asyncio
    async def test_create_calls_audit_create(self, repo, mock_session):
        """create() should call _audit_create after INSERT."""
        sale_id = uuid4()
        mock_session.execute.return_value.scalar_one.return_value = sale_id

        from src.market.domain.value_objects.sale_value_objects import (
            SaleCreateValueObject,
        )

        data = SaleCreateValueObject(
            user_id=uuid4(),
            buyer_id=uuid4(),
            animal_id=uuid4(),
            sale_date="2026-07-01",
            price=100.0,
            price_per_kg=10.0,
            weight=10.0,
            description="Test sale",
        )

        await repo.create(data)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "create"
        assert repo.audit_repository.record.call_args[1]["entity_type"] == "sale"

    @pytest.mark.asyncio
    async def test_update_data_calls_audit_update(self, repo, mock_session):
        """update_data() should call _audit_update after UPDATE."""
        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "price": 50.0,
            }
        )

        await repo.update_data(
            entity_id,
            buyer_id=uuid4(),
            animal_id=uuid4(),
            sale_date="2026-07-01",
            price=100.0,
            price_per_kg=10.0,
            weight=10.0,
            description="Updated",
        )

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "update"

    @pytest.mark.asyncio
    async def test_delete_calls_audit_delete(self, repo, mock_session):
        """delete() should call _audit_delete after DELETE."""
        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "price": 100.0,
            }
        )

        await repo.delete(entity_id)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "delete"


# ── 2.11 UserRepository ─────────────────────────────────────────────────────


class TestUserRepositoryAudit:
    """Task 2.11: UserRepository should call audit on CUD."""

    @pytest.fixture
    def repo(self, mock_session):
        from src.auth.infrastructure.persistence.repositories.user_repository import (
            UserRepository,
        )

        repo = UserRepository(mock_session)
        repo.audit_repository = MagicMock()
        repo.get_by_id = AsyncMock()
        repo.get_by_id.return_value = make_entity_mock()
        return repo

    @pytest.mark.asyncio
    async def test_create_calls_audit_create(self, repo, mock_session):
        """create() should call _audit_create after INSERT."""
        user_id = uuid4()
        mock_session.execute.return_value.scalar_one.return_value = user_id

        from src.auth.domain.value_objects.user_value_object import (
            UserCreationValueObject,
        )

        data = UserCreationValueObject(
            name="Test User",
            dni="12345678",
            email="test@test.com",
        )

        await repo.create(data, password="hashed_pwd")

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "create"
        assert repo.audit_repository.record.call_args[1]["entity_type"] == "user"

    @pytest.mark.asyncio
    async def test_update_data_calls_audit_update(self, repo, mock_session):
        """update_data() should call _audit_update."""
        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "name": "Old",
            }
        )

        from src.auth.domain.value_objects.user_value_object import (
            UserUpdateValueObject,
        )

        data = UserUpdateValueObject(name="New")
        await repo.update_data(entity_id, data)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "update"

    @pytest.mark.asyncio
    async def test_update_password_calls_audit_update(self, repo, mock_session):
        """update_password() should call _audit_update."""
        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "name": "Test",
            }
        )

        await repo.update_password(entity_id, "new_hashed_pwd")

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "update"

    @pytest.mark.asyncio
    async def test_update_role_calls_audit_update(self, repo, mock_session):
        """update_role() should call _audit_update."""
        from src.auth.domain.entities._user_role import UserRole

        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "name": "Test",
            }
        )

        await repo.update_role(entity_id, UserRole.EDITOR)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "update"


# ── 2.12 TenantRepository ───────────────────────────────────────────────────


class TestTenantRepositoryAudit:
    """Task 2.12: TenantRepository should call audit on create."""

    @pytest.fixture
    def repo(self, mock_session):
        from src.auth.infrastructure.persistence.repositories.tenant_repository import (
            TenantRepository,
        )

        repo = TenantRepository(mock_session)
        repo.audit_repository = MagicMock()
        repo.get_by_id = AsyncMock()
        repo.get_by_id.return_value = make_entity_mock()
        return repo

    @pytest.mark.asyncio
    async def test_create_calls_audit_create(self, repo, mock_session):
        """create() should call _audit_create after INSERT."""
        tenant_id = uuid4()
        mock_session.execute.return_value.scalar_one.return_value = tenant_id

        await repo.create(name="Test Tenant", slug="test-tenant")

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "create"
        assert repo.audit_repository.record.call_args[1]["entity_type"] == "tenant"


# ── 2.13 RefreshTokenRepository ──────────────────────────────────────────────


class TestRefreshTokenRepositoryAudit:
    """Task 2.13: RefreshTokenRepository should call audit on CUD."""

    @pytest.fixture
    def repo(self, mock_session):
        from src.auth.infrastructure.persistence.repositories.refresh_token_repository import (
            RefreshTokenRepository,
        )

        repo = RefreshTokenRepository(mock_session)
        repo.audit_repository = MagicMock()
        return repo

    @pytest.mark.asyncio
    async def test_save_calls_audit_create(self, repo):
        """save() should call _audit_create."""
        from src.auth.domain.entities import RefreshTokenEntity

        token = RefreshTokenEntity(
            id=uuid4(),
            user_id=uuid4(),
            token_hash="hash123",
            family_id=uuid4(),
            expires_at="2026-08-01",
            is_revoked=False,
        )

        await repo.save(token)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "create"
        assert repo.audit_repository.record.call_args[1]["entity_type"] == "refresh_token"

    @pytest.mark.asyncio
    async def test_revoke_token_calls_audit_update(self, repo, mock_session):
        """revoke_token() should call _audit_update."""
        entity_id = uuid4()
        mock_session.execute.return_value = make_old_row(
            {
                "id": entity_id,
                "revoked_at": None,
            }
        )

        await repo.revoke_token(entity_id)

        repo.audit_repository.record.assert_called_once()
        assert repo.audit_repository.record.call_args[1]["action"] == "update"

    @pytest.mark.asyncio
    async def test_revoke_family_calls_audit_update(self, repo, mock_session):
        """revoke_family() should call _audit_update per revoked token."""
        entity_id = uuid4()

        # SELECT old tokens returns one token
        # The repo calls old_rows.mappings().all(), so we need
        # select_result.mappings.return_value.all.return_value
        select_result = MagicMock()
        mappings_mock = MagicMock()
        mappings_mock.all.return_value = [
            make_row_dict({"id": entity_id, "revoked_at": None}),
        ]
        select_result.mappings.return_value = mappings_mock

        # UPDATE result (not inspected by repo)
        update_result = MagicMock()

        mock_session.execute.side_effect = [select_result, update_result]

        await repo.revoke_family(uuid4())

        assert repo.audit_repository.record.call_count >= 1
        assert repo.audit_repository.record.call_args[1]["action"] == "update"

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens_calls_audit_update(self, repo, mock_session):
        """revoke_all_user_tokens() should call _audit_update per revoked token."""
        entity_id = uuid4()

        select_result = MagicMock()
        mappings_mock = MagicMock()
        mappings_mock.all.return_value = [
            make_row_dict({"id": entity_id, "revoked_at": None}),
        ]
        select_result.mappings.return_value = mappings_mock

        update_result = MagicMock()

        mock_session.execute.side_effect = [select_result, update_result]

        await repo.revoke_all_user_tokens(uuid4())

        assert repo.audit_repository.record.call_count >= 1
        assert repo.audit_repository.record.call_args[1]["action"] == "update"
