"""
G1.2 — Unit tests for Timestamp Semantics

Tests:
- Instant creation and UTC enforcement
- Duration arithmetic
- Clock operations
- Clock drift detection
- Event timestamp validation
"""

import time
from datetime import datetime, timezone, timedelta
import pytest
from src.domain.time import Instant, Duration, Clock, ClockDriftDetector, validate_event_timestamp


class TestInstant:
    def test_now_creates_utc_instant(self):
        """Instant.now() should create a UTC timestamp."""
        instant = Instant.now()
        assert instant.dt.tzinfo == timezone.utc

    def test_from_datetime_converts_to_utc(self):
        """from_datetime should convert to UTC."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone(timedelta(hours=5)))
        instant = Instant.from_datetime(dt)
        assert instant.dt.tzinfo == timezone.utc
        assert instant.dt.hour == 5  # 10:30 +05:00 = 05:30 UTC

    def test_from_datetime_rejects_naive(self):
        """from_datetime should reject timezone-naive datetimes."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            Instant.from_datetime(dt)

    def test_from_unix_seconds(self):
        """from_unix_seconds should create correct instant."""
        instant = Instant.from_unix_seconds(1700000000.0)
        assert instant.dt.year == 2023

    def test_iso8601_format(self):
        """to_iso8601 should return ISO format string."""
        instant = Instant.now()
        iso = instant.to_iso8601()
        assert "T" in iso
        assert iso.endswith("+00:00")

    def test_comparison(self):
        """Instants should be comparable."""
        t1 = Instant.from_unix_seconds(1000.0)
        t2 = Instant.from_unix_seconds(2000.0)
        assert t1 < t2
        assert t2 > t1
        assert t1 <= t2
        assert t2 >= t1
        assert t1 != t2

    def test_immutable(self):
        """Instant should be immutable."""
        instant = Instant.now()
        with pytest.raises(Exception):
            instant._dt = datetime.now(timezone.utc)

    def test_hashable(self):
        """Instant should be hashable."""
        instant = Instant.now()
        d = {instant: "test"}
        assert d[instant] == "test"


class TestDuration:
    def test_from_seconds(self):
        """Duration.from_seconds should create correct duration."""
        d = Duration.from_seconds(1.5)
        assert d.seconds == 1.5

    def test_from_milliseconds(self):
        """Duration.from_milliseconds should create correct duration."""
        d = Duration.from_milliseconds(1500)
        assert d.milliseconds == 1500

    def test_from_nanoseconds(self):
        """Duration.from_nanoseconds should create correct duration."""
        d = Duration.from_nanoseconds(1_000_000_000)
        assert d.nanoseconds == 1_000_000_000
        assert d.seconds == 1.0

    def test_negative_duration_rejected(self):
        """Negative durations should be rejected."""
        with pytest.raises(ValueError, match="negative"):
            Duration(-1)

    def test_addition(self):
        """Durations should be addable."""
        d1 = Duration.from_seconds(1.0)
        d2 = Duration.from_seconds(2.0)
        d3 = d1 + d2
        assert d3.seconds == 3.0

    def test_subtraction(self):
        """Durations should be subtractable."""
        d1 = Duration.from_seconds(3.0)
        d2 = Duration.from_seconds(1.0)
        d3 = d1 - d2
        assert d3.seconds == 2.0

    def test_subtraction_negative_rejected(self):
        """Subtraction resulting in negative should be rejected."""
        d1 = Duration.from_seconds(1.0)
        d2 = Duration.from_seconds(2.0)
        with pytest.raises(ValueError, match="negative"):
            d1 - d2

    def test_multiplication(self):
        """Durations should be multipliable by non-negative integers."""
        d = Duration.from_seconds(1.0)
        d2 = d * 3
        assert d2.seconds == 3.0

    def test_multiplication_negative_rejected(self):
        """Multiplication by negative should be rejected."""
        d = Duration.from_seconds(1.0)
        with pytest.raises(ValueError, match="negative"):
            d * -1

    def test_comparison(self):
        """Durations should be comparable."""
        d1 = Duration.from_seconds(1.0)
        d2 = Duration.from_seconds(2.0)
        assert d1 < d2
        assert d2 > d1
        assert d1 <= d2
        assert d2 >= d1

    def test_hashable(self):
        """Duration should be hashable."""
        d = Duration.from_seconds(1.0)
        s = {d}
        assert d in s


class TestClock:
    def test_now_returns_instant(self):
        """Clock.now() should return an Instant."""
        instant = Clock.now()
        assert isinstance(instant, Instant)

    def test_monotonic_returns_float(self):
        """Clock.monotonic() should return a float."""
        t = Clock.monotonic()
        assert isinstance(t, float)

    def test_monotonic_ns_returns_int(self):
        """Clock.monotonic_ns() should return an int."""
        t = Clock.monotonic_ns()
        assert isinstance(t, int)

    def test_elapsed_since(self):
        """Clock.elapsed_since should return a Duration."""
        start = Clock.monotonic()
        time.sleep(0.01)
        elapsed = Clock.elapsed_since(start)
        assert isinstance(elapsed, Duration)
        assert elapsed.seconds > 0


class TestClockDriftDetector:
    def test_no_drift_within_tolerance(self):
        """Should detect no drift when within tolerance."""
        detector = ClockDriftDetector(max_drift_seconds=5.0)
        now = Clock.now()
        assert detector.check_drift(now) is True
        assert detector.drift_detected is False

    def test_drift_detected_beyond_tolerance(self):
        """Should detect drift when beyond tolerance."""
        detector = ClockDriftDetector(max_drift_seconds=1.0)
        future = Instant.from_unix_seconds(Clock.now().unix_seconds + 10.0)
        assert detector.check_drift(future) is False
        assert detector.drift_detected is True


class TestValidateEventTimestamp:
    def test_valid_timestamp(self):
        """Should accept timestamps within bounds."""
        now = Clock.now()
        occurred = Instant.from_unix_seconds(now.unix_seconds - 1.0)
        recorded = Instant.from_unix_seconds(now.unix_seconds)
        assert validate_event_timestamp(occurred, recorded) is True

    def test_future_timestamp_rejected(self):
        """Should reject timestamps too far in the future."""
        now = Clock.now()
        future = Instant.from_unix_seconds(now.unix_seconds + 100.0)
        recorded = Instant.from_unix_seconds(now.unix_seconds)
        assert validate_event_timestamp(future, recorded) is False

    def test_stale_timestamp_rejected(self):
        """Should reject timestamps too far in the past."""
        now = Clock.now()
        past = Instant.from_unix_seconds(now.unix_seconds - 7200.0)  # 2 hours ago
        recorded = Instant.from_unix_seconds(now.unix_seconds)
        assert validate_event_timestamp(past, recorded) is False

    def test_recorded_before_occurred_rejected(self):
        """Should reject when recorded_at < occurred_at."""
        now = Clock.now()
        occurred = Instant.from_unix_seconds(now.unix_seconds)
        recorded = Instant.from_unix_seconds(now.unix_seconds - 1.0)
        assert validate_event_timestamp(occurred, recorded) is False
