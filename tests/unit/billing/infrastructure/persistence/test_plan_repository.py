"""Tests for PlanRepository — seed data implementation."""

from decimal import Decimal

import pytest

from src.billing.domain.entities._plan import Plan
from src.billing.domain.entities._plan_type import PlanType


class TestPlanRepository:
    """PlanRepository returns seed data from in-memory dict."""

    def test_import_succeeds(self) -> None:
        """PlanRepository can be imported."""

    def setup_method(self) -> None:
        from src.billing.infrastructure.persistence.repositories._plan_repository import (
            PlanRepository,
        )

        self.repo = PlanRepository()

    @pytest.mark.asyncio
    async def test_get_by_plan_type_free(self) -> None:
        """get_by_plan_type(FREE) returns FREE plan."""
        plan = await self.repo.get_by_plan_type(PlanType.FREE)
        assert plan.plan_type == PlanType.FREE
        assert plan.name == "Free"

    @pytest.mark.asyncio
    async def test_get_by_plan_type_pro(self) -> None:
        """get_by_plan_type(PRO) returns PRO plan."""
        plan = await self.repo.get_by_plan_type(PlanType.PRO)
        assert plan.plan_type == PlanType.PRO
        assert plan.name == "Pro"

    @pytest.mark.asyncio
    async def test_get_by_plan_type_enterprise(self) -> None:
        """get_by_plan_type(ENTERPRISE) returns ENTERPRISE plan."""
        plan = await self.repo.get_by_plan_type(PlanType.ENTERPRISE)
        assert plan.plan_type == PlanType.ENTERPRISE
        assert plan.name == "Enterprise"

    @pytest.mark.asyncio
    async def test_list_all_returns_three_plans(self) -> None:
        """list_all() returns exactly 3 plans."""
        plans = await self.repo.list_all()
        assert len(plans) == 3

    @pytest.mark.asyncio
    async def test_list_all_contains_all_types(self) -> None:
        """list_all() includes FREE, PRO, and ENTERPRISE."""
        plans = await self.repo.list_all()
        plan_types = {p.plan_type for p in plans}
        assert plan_types == {PlanType.FREE, PlanType.PRO, PlanType.ENTERPRISE}

    @pytest.mark.asyncio
    async def test_get_by_id_returns_correct_plan(self) -> None:
        """get_by_id returns a plan by its UUID."""
        plans = await self.repo.list_all()
        target = plans[0]
        result = await self.repo.get_by_id(target.id)
        assert result is not None
        assert result.id == target.id
        assert result.plan_type == target.plan_type

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_unknown(self) -> None:
        """get_by_id returns None for non-existent UUID."""
        from uuid import uuid4

        result = await self.repo.get_by_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_plan_type_uses_type_safe_lookup(self) -> None:
        """get_by_plan_type uses PlanType enum, not string."""
        plan = await self.repo.get_by_plan_type(PlanType.FREE)
        assert isinstance(plan, Plan)
        assert plan.plan_type is PlanType.FREE

    @pytest.mark.asyncio
    async def test_free_plan_has_zero_price(self) -> None:
        """FREE plan has price_monthly=0.00 and no yearly price."""
        plan = await self.repo.get_by_plan_type(PlanType.FREE)
        assert plan.price_monthly is not None
        assert plan.price_monthly.amount == Decimal("0.00")
        assert plan.price_yearly is None

    @pytest.mark.asyncio
    async def test_pro_plan_has_prices(self) -> None:
        """PRO plan has monthly=15.00 and yearly=150.00."""
        plan = await self.repo.get_by_plan_type(PlanType.PRO)
        assert plan.price_monthly is not None
        assert plan.price_yearly is not None
        assert plan.price_monthly.amount == Decimal("15.00")
        assert plan.price_yearly.amount == Decimal("150.00")

    @pytest.mark.asyncio
    async def test_enterprise_plan_has_prices(self) -> None:
        """ENTERPRISE plan has monthly=50.00 and yearly=500.00."""
        plan = await self.repo.get_by_plan_type(PlanType.ENTERPRISE)
        assert plan.price_monthly is not None
        assert plan.price_yearly is not None
        assert plan.price_monthly.amount == Decimal("50.00")
        assert plan.price_yearly.amount == Decimal("500.00")

    @pytest.mark.asyncio
    async def test_repo_is_plan_repository_port(self) -> None:
        """PlanRepository implements IPlanRepository."""
        from src.billing.domain.repositories import IPlanRepository

        assert isinstance(self.repo, IPlanRepository)
