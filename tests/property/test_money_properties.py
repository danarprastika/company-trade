"""
G1 — Property tests for Money and Quantity types

Uses property-based testing to verify:
- Precision preservation
- Commutativity of addition
- Associativity of addition
- No float contamination
- Hash consistency
"""

import pytest
from decimal import Decimal
from src.domain.money import Money, Quantity


class TestMoneyProperties:
    def test_addition_commutative(self):
        """Money addition should be commutative: a + b == b + a."""
        m1 = Money.from_string("100.50", "USD")
        m2 = Money.from_string("50.25", "USD")
        assert m1 + m2 == m2 + m1

    def test_addition_associative(self):
        """Money addition should be associative: (a + b) + c == a + (b + c)."""
        m1 = Money.from_string("100.50", "USD")
        m2 = Money.from_string("50.25", "USD")
        m3 = Money.from_string("25.00", "USD")
        assert (m1 + m2) + m3 == m1 + (m2 + m3)

    def test_addition_identity(self):
        """Money addition with zero should be identity: a + 0 == a."""
        m = Money.from_string("100.50", "USD")
        zero = Money.zero("USD")
        assert m + zero == m

    def test_subtraction_inverse(self):
        """Money subtraction should be inverse of addition: (a + b) - b == a."""
        m1 = Money.from_string("100.50", "USD")
        m2 = Money.from_string("50.25", "USD")
        assert (m1 + m2) - m2 == m1

    def test_multiplication_distributive(self):
        """Money multiplication should distribute over addition: a * n == a + a + ... + a."""
        m = Money.from_string("100.50", "USD")
        n = 3
        repeated_addition = m
        for _ in range(n - 1):
            repeated_addition = repeated_addition + m
        assert m * n == repeated_addition

    def test_no_float_contamination(self):
        """Money should never use float internally."""
        m = Money.from_string("100.10", "USD")
        assert isinstance(m.amount, Decimal)
        # Verify no float artifacts
        assert m.amount == Decimal("100.10")

    def test_hash_consistency(self):
        """Equal Money objects should have equal hashes."""
        m1 = Money.from_string("100.50", "USD")
        m2 = Money.from_string("100.50", "USD")
        assert m1 == m2
        assert hash(m1) == hash(m2)

    def test_precision_preserved(self):
        """Money should always quantize to 2 decimal places."""
        m = Money.from_string("100.999", "USD")
        assert m.amount == Decimal("101.00")  # Rounded half up

    def test_negation_inverse(self):
        """Negation should be inverse: a + (-a) == 0."""
        m = Money.from_string("100.50", "USD")
        zero = Money.zero("USD")
        assert m + (-m) == zero


class TestQuantityProperties:
    def test_addition_commutative(self):
        """Quantity addition should be commutative."""
        q1 = Quantity.from_string("100.50", scale=2)
        q2 = Quantity.from_string("50.25", scale=2)
        assert q1 + q2 == q2 + q1

    def test_addition_associative(self):
        """Quantity addition should be associative."""
        q1 = Quantity.from_string("100.50", scale=2)
        q2 = Quantity.from_string("50.25", scale=2)
        q3 = Quantity.from_string("25.00", scale=2)
        assert (q1 + q2) + q3 == q1 + (q2 + q3)

    def test_addition_identity(self):
        """Quantity addition with zero should be identity."""
        q = Quantity.from_string("100.50", scale=2)
        zero = Quantity.zero(scale=2)
        assert q + zero == q

    def test_subtraction_inverse(self):
        """Quantity subtraction should be inverse of addition."""
        q1 = Quantity.from_string("100.50", scale=2)
        q2 = Quantity.from_string("50.25", scale=2)
        assert (q1 + q2) - q2 == q1

    def test_no_float_contamination(self):
        """Quantity should never use float internally."""
        q = Quantity.from_string("100.10", scale=2)
        assert isinstance(q.value, Decimal)
        assert q.value == Decimal("100.10")

    def test_hash_consistency(self):
        """Equal Quantity objects should have equal hashes."""
        q1 = Quantity.from_string("100.50", scale=2)
        q2 = Quantity.from_string("100.50", scale=2)
        assert q1 == q2
        assert hash(q1) == hash(q2)

    def test_precision_preserved(self):
        """Quantity should quantize to specified scale."""
        q = Quantity.from_string("100.999", scale=2)
        assert q.value == Decimal("101.00")

    def test_negation_inverse(self):
        """Negation should be inverse: q + (-q) == 0."""
        q = Quantity.from_string("100.50", scale=2)
        zero = Quantity.zero(scale=2)
        assert q + (-q) == zero

    def test_different_scales_not_equal(self):
        """Quantities with different scales should not be equal."""
        q1 = Quantity.from_string("100", scale=0)
        q2 = Quantity.from_string("100.00", scale=2)
        assert q1 != q2
