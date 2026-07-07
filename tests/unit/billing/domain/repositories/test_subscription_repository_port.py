"""Tests for ISubscriptionRepository port interface."""

from abc import ABC
from uuid import UUID

import pytest

from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.repositories._subscription_repository_port import (
    ISubscriptionRepository,
)


class TestISubscriptionRepository:
    """Task 1.9: ISubscriptionRepository port interface.

    Tests that the port can be implemented (ABC enforcement).
    """

    def test_is_abstract(self) -> None:
        """ISubscriptionRepository should not be instantiable directly."""
        with pytest.raises(TypeError):
            ISubscriptionRepository()  # type: ignore[abstract]

    def test_can_be_implemented(self) -> None:
        """A concrete class should be able to implement ISubscriptionRepository."""

        class ConcreteSubscriptionRepository(ISubscriptionRepository):
            async def create(self, subscription: Subscription) -> Subscription:
                raise NotImplementedError

            async def update(self, subscription: Subscription) -> Subscription:
                raise NotImplementedError

            async def get_by_tenant(self, tenant_id: UUID) -> Subscription | None:
                raise NotImplementedError

            async def get_by_id(self, id: UUID) -> Subscription | None:
                raise NotImplementedError

            async def list_expired_trials(self) -> list[Subscription]:
                raise NotImplementedError

            async def list_active_near_period_end(self, days_ahead: int) -> list[Subscription]:
                raise NotImplementedError

        repo = ConcreteSubscriptionRepository()
        assert isinstance(repo, ISubscriptionRepository)
        assert isinstance(repo, ABC)
