from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MoneyVO:
    amount: Decimal
    currency: str = "ARS"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"El monto no puede ser negativo, se recibió {self.amount}")
        if not self.currency:
            raise ValueError("La moneda no puede estar vacía")

    def __add__(self, other: MoneyVO) -> MoneyVO:
        if self.currency != other.currency:
            raise ValueError(f"No se puede sumar {self.currency} a {other.currency}")
        return MoneyVO(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: MoneyVO) -> MoneyVO:
        if self.currency != other.currency:
            raise ValueError(f"No se puede restar {other.currency} de {self.currency}")
        return MoneyVO(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, scalar: Decimal | int | float) -> MoneyVO:
        if not isinstance(scalar, Decimal):
            scalar = Decimal(str(scalar))
        return MoneyVO(amount=self.amount * scalar, currency=self.currency)

    def __neg__(self) -> MoneyVO:
        return MoneyVO(amount=-self.amount, currency=self.currency)


@dataclass(frozen=True)
class PaymentMethodVO:
    card_brand: str | None = None
    payment_type_id: str | None = None
