"""Tests for IPlanRepository port interface."""

from abc import ABC
from uuid import UUID

import pytest

from src.billing.domain.entities._plan import Plan
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.repositories._plan_repository_port import IPlanRepository


class TestIPlanRepository:
    """Task 1.8: IPlanRepository port interface.

    Tests that the port can be implemented (ABC enforcement).
    """

    def test_is_abstract(self) -> None:
        """IPlanRepository should not be instantiable directly."""
        with pytest.raises(TypeError):
            IPlanRepository()  # type: ignore[abstract]

    def test_can_be_implemented(self) -> None:
        """A concrete class should be able to implement IPlanRepository."""

        class ConcretePlanRepository(IPlanRepository):
            async def get_by_plan_type(self, plan_type: PlanType) -> Plan:
                raise NotImplementedError

            async def get_by_id(self, id: UUID) -> Plan | None:
                raise NotImplementedError

            async def list_all(self) -> list[Plan]:
                raise NotImplementedError

        repo = ConcretePlanRepository()
        assert isinstance(repo, IPlanRepository)
        assert isinstance(repo, ABC)
