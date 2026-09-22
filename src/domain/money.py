"""
G1.3 — Money and Quantity Types

Fixed-precision decimal types for monetary and quantity calculations.
Never use binary floating point for authoritative accounting.

Specification references:
- FINAL_SPECIFICATION/05_DATABASE_CANONICAL_MODEL.md:
  "Money/quantity calculations use fixed-precision decimal semantics, never binary floating point for authoritative accounting."
- docs/03_domains/04_PORTFOLIO_RISK_MODEL.md (exposure, concentration, leverage)
- docs/06_trading/06_TCA.md (net outcome distinguishes gross P&L from fees, spread, slippage)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union

# Default precision for monetary values (e.g., USD has 2 decimal places)
DEFAULT_MONEY_SCALE = 2
# Default precision for quantities (e.g., stock shares have 0 decimal places)
DEFAULT_QUANTITY_SCALE = 0


@dataclass(frozen=True)
class Money:
    """
    Fixed-precision monetary value with currency code.
    Uses Decimal for exact arithmetic, never float.
    """

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError(f"Money amount must be Decimal, got {type(self.amount).__name__}")
        if not isinstance(self.currency, str) or len(self.currency) != 3:
            raise ValueError(f"Currency must be a 3-letter ISO code, got {self.currency!r}")
        # Quantize to standard money scale
        object.__setattr__(self, "amount", self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @classmethod
    def from_string(cls, amount: str, currency: str) -> "Money":
        """Create Money from string amount and currency code."""
        return cls(Decimal(amount), currency)

    @classmethod
    def from_float(cls, amount: float, currency: str) -> "Money":
        """Create Money from float (converts to Decimal via string to avoid float artifacts)."""
        return cls(Decimal(str(amount)), currency)

    @classmethod
    def zero(cls, currency: str) -> "Money":
        """Create zero-value Money."""
        return cls(Decimal("0"), currency)

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {other.currency} from {self.currency}")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Union[int, Decimal]) -> "Money":
        if isinstance(factor, float):
            raise TypeError("Cannot multiply Money by float; use int or Decimal")
        return Money(self.amount * Decimal(factor), self.currency)

    def __rmul__(self, factor: Union[int, Decimal]) -> "Money":
        return self.__mul__(factor)

    def __truediv__(self, divisor: Union[int, Decimal]) -> "Money":
        if isinstance(divisor, float):
            raise TypeError("Cannot divide Money by float; use int or Decimal")
        return Money(self.amount / Decimal(divisor), self.currency)

    def __neg__(self) -> "Money":
        return Money(-self.amount, self.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} with {other.currency}")
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} with {other.currency}")
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} with {other.currency}")
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} with {other.currency}")
        return self.amount >= other.amount

    def __hash__(self) -> int:
        return hash((self.amount, self.currency))

    def __repr__(self) -> str:
        return f"Money({self.amount}, '{self.currency}')"

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"


@dataclass(frozen=True)
class Quantity:
    """
    Fixed-precision quantity value.
    Uses Decimal for exact arithmetic, never float.
    Scale is configurable per instrument (e.g., 0 for stocks, 8 for crypto).
    """

    value: Decimal
    scale: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise TypeError(f"Quantity value must be Decimal, got {type(self.value).__name__}")
        if not isinstance(self.scale, int) or self.scale < 0:
            raise ValueError(f"Scale must be a non-negative integer, got {self.scale!r}")
        # Quantize to the specified scale
        quantizer = Decimal("1")
        for _ in range(self.scale):
            quantizer = quantizer / Decimal("10")
        object.__setattr__(self, "value", self.value.quantize(quantizer, rounding=ROUND_HALF_UP))

    @classmethod
    def from_string(cls, value: str, scale: int = DEFAULT_QUANTITY_SCALE) -> "Quantity":
        """Create Quantity from string value and scale."""
        return cls(Decimal(value), scale)

    @classmethod
    def from_float(cls, value: float, scale: int = DEFAULT_QUANTITY_SCALE) -> "Quantity":
        """Create Quantity from float (converts to Decimal via string)."""
        return cls(Decimal(str(value)), scale)

    @classmethod
    def zero(cls, scale: int = DEFAULT_QUANTITY_SCALE) -> "Quantity":
        """Create zero-value Quantity."""
        return cls(Decimal("0"), scale)

    def __add__(self, other: "Quantity") -> "Quantity":
        if self.scale != other.scale:
            raise ValueError(f"Cannot add Quantity with scale {self.scale} to scale {other.scale}")
        return Quantity(self.value + other.value, self.scale)

    def __sub__(self, other: "Quantity") -> "Quantity":
        if self.scale != other.scale:
            raise ValueError(f"Cannot subtract Quantity with scale {self.scale} from scale {other.scale}")
        result = self.value - other.value
        return Quantity(result, self.scale)

    def __mul__(self, factor: Union[int, Decimal]) -> "Quantity":
        if isinstance(factor, float):
            raise TypeError("Cannot multiply Quantity by float; use int or Decimal")
        return Quantity(self.value * Decimal(factor), self.scale)

    def __rmul__(self, factor: Union[int, Decimal]) -> "Quantity":
        return self.__mul__(factor)

    def __truediv__(self, divisor: Union[int, Decimal]) -> "Quantity":
        if isinstance(divisor, float):
            raise TypeError("Cannot divide Quantity by float; use int or Decimal")
        return Quantity(self.value / Decimal(divisor), self.scale)

    def __neg__(self) -> "Quantity":
        return Quantity(-self.value, self.scale)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        return self.value == other.value and self.scale == other.scale

    def __lt__(self, other: "Quantity") -> bool:
        if self.scale != other.scale:
            raise ValueError(f"Cannot compare Quantity with scale {self.scale} to scale {other.scale}")
        return self.value < other.value

    def __le__(self, other: "Quantity") -> bool:
        if self.scale != other.scale:
            raise ValueError(f"Cannot compare Quantity with scale {self.scale} to scale {other.scale}")
        return self.value <= other.value

    def __gt__(self, other: "Quantity") -> bool:
        if self.scale != other.scale:
            raise ValueError(f"Cannot compare Quantity with scale {self.scale} to scale {other.scale}")
        return self.value > other.value

    def __ge__(self, other: "Quantity") -> bool:
        if self.scale != other.scale:
            raise ValueError(f"Cannot compare Quantity with scale {self.scale} to scale {other.scale}")
        return self.value >= other.value

    def __hash__(self) -> int:
        return hash((self.value, self.scale))

    def __repr__(self) -> str:
        return f"Quantity({self.value}, scale={self.scale})"

    def __str__(self) -> str:
        return str(self.value)

    def is_zero(self) -> bool:
        return self.value == Decimal("0")

    def is_positive(self) -> bool:
        return self.value > Decimal("0")

    def is_negative(self) -> bool:
        return self.value < Decimal("0")


__all__ = [
    "Money",
    "Quantity",
    "DEFAULT_MONEY_SCALE",
    "DEFAULT_QUANTITY_SCALE",
]
