"""
G1.2 — Timestamp Semantics

UTC timestamps with nanosecond precision and monotonic duration semantics.
Clock drift detection and event timestamp validation.

Specification references:
- FINAL_SPECIFICATION/02_RUNTIME_CONTRACTS.md (occurred_at_utc, recorded_at_utc, issued_at_utc)
- docs/09_infrastructure/02_CLOCK_SYNC.md (NTP/clock sync, drift detection, monotonic timing)
- docs/02_architecture/03_EVENT_ARCHITECTURE.md (event envelope timestamps)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class Instant:
    """
    A point in time represented as UTC with nanosecond precision.
    Uses Python's datetime with timezone.utc.
    """

    _dt: datetime

    def __post_init__(self) -> None:
        if self._dt.tzinfo is None:
            raise ValueError("Instant must be timezone-aware (UTC)")
        if self._dt.tzinfo != timezone.utc:
            raise ValueError("Instant must be in UTC")

    @classmethod
    def now(cls) -> "Instant":
        """Create an Instant representing the current UTC time."""
        return cls(datetime.now(timezone.utc))

    @classmethod
    def from_datetime(cls, dt: datetime) -> "Instant":
        """Create an Instant from a datetime, converting to UTC if needed."""
        if dt.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        return cls(dt.astimezone(timezone.utc))

    @classmethod
    def from_unix_seconds(cls, seconds: float) -> "Instant":
        """Create an Instant from Unix timestamp (seconds since epoch)."""
        return cls(datetime.fromtimestamp(seconds, tz=timezone.utc))

    @property
    def dt(self) -> datetime:
        """Return the underlying datetime in UTC."""
        return self._dt

    @property
    def unix_seconds(self) -> float:
        """Return Unix timestamp in seconds."""
        return self._dt.timestamp()

    def to_iso8601(self) -> str:
        """Return ISO 8601 string representation."""
        return self._dt.isoformat()

    def __str__(self) -> str:
        return self.to_iso8601()

    def __lt__(self, other: "Instant") -> bool:
        return self._dt < other._dt

    def __le__(self, other: "Instant") -> bool:
        return self._dt <= other._dt

    def __gt__(self, other: "Instant") -> bool:
        return self._dt > other._dt

    def __ge__(self, other: "Instant") -> bool:
        return self._dt >= other._dt

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Instant):
            return NotImplemented
        return self._dt == other._dt

    def __hash__(self) -> int:
        return hash(self._dt)


@dataclass(frozen=True)
class Duration:
    """
    A duration of time using monotonic clock semantics.
    Durations are used for measuring elapsed time, not for representing points in time.
    """

    _nanoseconds: int

    def __post_init__(self) -> None:
        if self._nanoseconds < 0:
            raise ValueError("Duration cannot be negative")

    @classmethod
    def from_seconds(cls, seconds: float) -> "Duration":
        """Create a Duration from seconds (float)."""
        nanos = int(seconds * 1_000_000_000)
        return cls(nanos)

    @classmethod
    def from_milliseconds(cls, ms: float) -> "Duration":
        """Create a Duration from milliseconds."""
        return cls(int(ms * 1_000_000))

    @classmethod
    def from_nanoseconds(cls, nanos: int) -> "Duration":
        """Create a Duration from nanoseconds."""
        return cls(nanos)

    @property
    def nanoseconds(self) -> int:
        return self._nanoseconds

    @property
    def microseconds(self) -> float:
        return self._nanoseconds / 1_000

    @property
    def milliseconds(self) -> float:
        return self._nanoseconds / 1_000_000

    @property
    def seconds(self) -> float:
        return self._nanoseconds / 1_000_000_000

    def __add__(self, other: "Duration") -> "Duration":
        return Duration(self._nanoseconds + other._nanoseconds)

    def __sub__(self, other: "Duration") -> "Duration":
        result = self._nanoseconds - other._nanoseconds
        if result < 0:
            raise ValueError("Duration subtraction would result in negative value")
        return Duration(result)

    def __mul__(self, factor: int) -> "Duration":
        if factor < 0:
            raise ValueError("Duration multiplication factor cannot be negative")
        return Duration(self._nanoseconds * factor)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return NotImplemented
        return self._nanoseconds == other._nanoseconds

    def __lt__(self, other: "Duration") -> bool:
        return self._nanoseconds < other._nanoseconds

    def __le__(self, other: "Duration") -> bool:
        return self._nanoseconds <= other._nanoseconds

    def __gt__(self, other: "Duration") -> bool:
        return self._nanoseconds > other._nanoseconds

    def __ge__(self, other: "Duration") -> bool:
        return self._nanoseconds >= other._nanoseconds

    def __hash__(self) -> int:
        return hash(self._nanoseconds)

    def __repr__(self) -> str:
        return f"Duration({self._nanoseconds}ns)"


class Clock:
    """
    Clock abstraction for time-related operations.
    Supports monotonic timing for durations and UTC for instants.
    """

    @staticmethod
    def now() -> Instant:
        """Return current UTC time."""
        return Instant.now()

    @staticmethod
    def monotonic() -> float:
        """Return monotonic time in seconds (for duration measurement)."""
        return time.monotonic()

    @staticmethod
    def monotonic_ns() -> int:
        """Return monotonic time in nanoseconds."""
        return time.monotonic_ns()

    @staticmethod
    def elapsed_since(start_monotonic: float) -> Duration:
        """Calculate elapsed duration since a monotonic timestamp."""
        elapsed = time.monotonic() - start_monotonic
        return Duration.from_seconds(elapsed)


class ClockDriftDetector:
    """
    Detects clock drift between system time and a reference time source.
    Per CLOCK_SYNC.md: "NTP/clock sync, drift detection, monotonic timing for durations, event timestamp validation."
    """

    def __init__(self, max_drift_seconds: float = 1.0) -> None:
        self._max_drift_seconds = max_drift_seconds
        self._last_check: Optional[Instant] = None
        self._drift_detected: bool = False

    def check_drift(self, reference_time: Optional[Instant] = None) -> bool:
        """
        Check if system clock has drifted beyond acceptable threshold.
        Returns True if drift is within acceptable bounds.
        """
        system_time = Clock.now()
        if reference_time is None:
            reference_time = system_time

        drift = abs((system_time - reference_time).total_seconds())
        self._drift_detected = drift > self._max_drift_seconds
        self._last_check = system_time
        return not self._drift_detected

    @property
    def drift_detected(self) -> bool:
        return self._drift_detected

    @property
    def max_drift_seconds(self) -> float:
        return self._max_drift_seconds


def validate_event_timestamp(
    occurred_at: Instant,
    recorded_at: Instant,
    max_future_tolerance_seconds: float = 5.0,
    max_past_tolerance_seconds: float = 3600.0,
) -> bool:
    """
    Validate that an event timestamp is within acceptable bounds.
    Per CLOCK_SYNC.md: "event timestamp validation."

    - occurred_at must not be too far in the future (clock skew)
    - occurred_at must not be too far in the past (stale data)
    - recorded_at must be >= occurred_at
    """
    now = Clock.now()

    future_diff = (occurred_at - now).total_seconds()
    if future_diff > max_future_tolerance_seconds:
        return False

    past_diff = (now - occurred_at).total_seconds()
    if past_diff > max_past_tolerance_seconds:
        return False

    if recorded_at < occurred_at:
        return False

    return True


__all__ = [
    "Instant",
    "Duration",
    "Clock",
    "ClockDriftDetector",
    "validate_event_timestamp",
]
