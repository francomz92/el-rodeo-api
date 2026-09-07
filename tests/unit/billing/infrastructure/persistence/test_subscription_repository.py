"""Tests for SubscriptionRepository — SQLAlchemy Core implementation."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.repositories import ISubscriptionRepository
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)


class TestSubscriptionRepository:
    """SubscriptionRepository CRUD with mocked session."""

    def setup_method(self) -> None:
        from src.billing.infrastructure.persistence.repositories._subscription_repository import (  # noqa: E501
            SubscriptionRepository,
        )

        self.session = MagicMock()
        self.session.execute = AsyncMock()
        self.repo = SubscriptionRepository(session=self.session)

    @pytest.mark.asyncio
    async def test_create_returns_subscription_entity(self) -> None:
        """create() persists a subscription and returns Subscription."""
        from datetime import datetime, timezone

        from src.billing.domain.entities._subscription import Subscription

        fake_id = uuid4()
        tenant_id = uuid4()
        plan_id = uuid4()
        now = datetime.now(tz=timezone.utc)

        # Mock execute to return new id
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = fake_id
        self.session.execute.return_value = result_mock

        # Mock get_by_id to return the entity
        expected_entity = Subscription(
            id=fake_id,
            tenant_id=tenant_id,
            plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now,
        )
        self.repo.get_by_id = AsyncMock(return_value=expected_entity)  # type: ignore

        sub = Subscription(
            id=fake_id,
            tenant_id=tenant_id,
            plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now,
        )
        entity = await self.repo.create(sub)

        assert entity.id == fake_id
        assert entity.tenant_id == tenant_id
        assert entity.plan_id == plan_id
        assert entity.status == SubscriptionStatus.ACTIVE
        self.session.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_by_tenant_returns_subscription(self) -> None:
        """get_by_tenant returns subscription for a tenant."""
        from datetime import datetime, timezone

        tenant_id = uuid4()
        fake_id = uuid4()
        plan_id = uuid4()
        now = datetime.now(tz=timezone.utc)

        # Mock session.execute to return a row mapping
        result_mock = MagicMock()
        row_mock = MagicMock()
        row_data = {
            "id": fake_id,
            "tenant_id": tenant_id,
            "plan_id": plan_id,
            "status": "active",
            "current_period_start": now,
            "current_period_end": now,
            "trial_end": None,
            "canceled_at": None,
            "subscription_metadata": {},
        }
        row_mock.__getitem__.side_effect = lambda k: row_data[k]
        row_mock.get.side_effect = lambda k, default=None: row_data.get(k, default)
        result_mock.mappings.return_value.one_or_none.return_value = row_mock
        self.session.execute.return_value = result_mock

        entity = await self.repo.get_by_tenant(tenant_id)

        assert entity is not None
        assert entity.id == fake_id
        assert entity.tenant_id == tenant_id
        assert entity.plan_id == plan_id
        assert entity.status == SubscriptionStatus.ACTIVE
        self.session.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_by_tenant_returns_none_when_not_found(self) -> None:
        """get_by_tenant returns None when no subscription exists."""

        result_mock = MagicMock()
        result_mock.mappings.return_value.one_or_none.return_value = None
        self.session.execute.return_value = result_mock

        entity = await self.repo.get_by_tenant(uuid4())

        assert entity is None

    @pytest.mark.asyncio
    async def test_get_by_id_returns_subscription(self) -> None:
        """get_by_id returns subscription by UUID."""
        from datetime import datetime, timezone

        sub_id = uuid4()
        tenant_id = uuid4()
        plan_id = uuid4()
        now = datetime.now(tz=timezone.utc)

        result_mock = MagicMock()
        row_mock = MagicMock()
        row_data = {
            "id": sub_id,
            "tenant_id": tenant_id,
            "plan_id": plan_id,
            "status": "active",
            "current_period_start": now,
            "current_period_end": now,
            "trial_end": None,
            "canceled_at": None,
            "subscription_metadata": {},
        }
        row_mock.__getitem__.side_effect = lambda k: row_data[k]
        row_mock.get.side_effect = lambda k, default=None: row_data.get(k, default)
        result_mock.mappings.return_value.one_or_none.return_value = row_mock
        self.session.execute.return_value = result_mock

        entity = await self.repo.get_by_id(sub_id)

        assert entity is not None
        assert entity.id == sub_id
        assert entity.tenant_id == tenant_id
        assert entity.status == SubscriptionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self) -> None:
        """get_by_id returns None when ID not found."""
        result_mock = MagicMock()
        result_mock.mappings.return_value.one_or_none.return_value = None
        self.session.execute.return_value = result_mock

        entity = await self.repo.get_by_id(uuid4())

        assert entity is None

    @pytest.mark.asyncio
    async def test_update_modifies_status(self) -> None:
        """update() changes subscription status and returns updated entity."""
        from datetime import datetime, timezone

        sub_id = uuid4()
        tenant_id = uuid4()
        plan_id = uuid4()
        now = datetime.now(tz=timezone.utc)

        # Mock the update execution
        result_mock = MagicMock()
        self.session.execute.return_value = result_mock

        # Mock get_by_id to return updated entity
        updated_entity = Subscription(
            id=sub_id,
            tenant_id=tenant_id,
            plan_id=plan_id,
            status=SubscriptionStatus.CANCELED,
            current_period_start=now,
            canceled_at=now,
        )
        self.repo.get_by_id = AsyncMock(return_value=updated_entity)  # type: ignore

        sub = Subscription(
            id=sub_id,
            tenant_id=tenant_id,
            plan_id=plan_id,
            status=SubscriptionStatus.CANCELED,
            current_period_start=now,
            canceled_at=now,
        )
        entity = await self.repo.update(sub)

        assert entity.status == SubscriptionStatus.CANCELED
        assert entity.canceled_at == now
        self.session.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_repo_is_tenant_aware(self) -> None:
        """SubscriptionRepository is a TenantAwareRepository."""

        assert isinstance(self.repo, TenantAwareRepository)

    @pytest.mark.asyncio
    async def test_repo_is_subscription_repository_port(self) -> None:
        """SubscriptionRepository implements ISubscriptionRepository."""

        assert isinstance(self.repo, ISubscriptionRepository)

    # ── Phase 0b: get_by_gateway_subscription_id ─────────────────────────────────

    def test_has_get_by_gateway_subscription_id_method(self) -> None:
        """SubscriptionRepository implements get_by_gateway_subscription_id."""
        assert hasattr(self.repo, "get_by_gateway_subscription_id")

    @pytest.mark.asyncio
    async def test_get_by_gateway_subscription_id_returns_subscription(self) -> None:
        """get_by_gateway_subscription_id returns a subscription when found."""
        gw_sub_id = "preapp-123"
        row_data = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "plan_id": uuid4(),
            "status": "active",
            "current_period_start": datetime.now(timezone.utc),
            "current_period_end": datetime.now(timezone.utc),
            "trial_end": None,
            "canceled_at": None,
            "subscription_metadata": {},
            "gateway_preference_id": None,
            "gateway_subscription_id": gw_sub_id,
            "billing_date": None,
            "next_billing_date": None,
            "gateway_card_id": None,
        }
        row = MagicMock()
        row.__getitem__.side_effect = lambda k: row_data[k]
        row.get.side_effect = lambda k, default=None: row_data.get(k, default)
        result_mock = MagicMock()
        result_mock.mappings.return_value.one_or_none.return_value = row
        self.session.execute.return_value = result_mock

        entity = await self.repo.get_by_gateway_subscription_id(gw_sub_id)

        assert entity is not None
        assert entity.gateway_subscription_id == gw_sub_id
        assert entity.id == row_data["id"]
        assert entity.status == SubscriptionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_by_gateway_subscription_id_returns_none(self) -> None:
        """get_by_gateway_subscription_id returns None when not found."""
        result_mock = MagicMock()
        result_mock.mappings.return_value.one_or_none.return_value = None
        self.session.execute.return_value = result_mock

        entity = await self.repo.get_by_gateway_subscription_id("preapp-unknown")
        assert entity is None
