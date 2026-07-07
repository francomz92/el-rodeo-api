"""Tests for Money value object."""

from decimal import Decimal

from src.billing.domain.value_objects._money import Money


class TestMoney:
    """Task 1.5: Money value object."""

    def test_construct(self) -> None:
        money = Money(amount=Decimal("29.99"), currency="ARS")
        assert money.amount == Decimal("29.99")
        assert money.currency == "ARS"

    def test_default_currency(self) -> None:
        money = Money(amount=Decimal("100.00"))
        assert money.currency == "ARS"

    def test_zero_amount(self) -> None:
        money = Money(amount=Decimal("0"))
        assert money.amount == Decimal("0")
        assert money.currency == "ARS"
