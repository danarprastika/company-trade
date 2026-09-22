"""
G1.4 — Instrument Model

Canonical instrument identity with precision, tick size, and market rules.

Specification references:
- docs/03_domains/01_MARKET_DOMAIN.md:
  "Canonical identifiers, precision, trading hours and market-specific rules are authoritative."
  Entities: Market, Instrument, Venue, Session, Calendar, ContractSpec.
- FINAL_SPECIFICATION/05_DATABASE_CANONICAL_MODEL.md:
  Market/Data: Market, Venue, Instrument, InstrumentVersion, MarketSession, Provider, ...
- docs/05_data_market/00_DATA_CONTRACTS.md:
  "Required metadata: Source, symbol/instrument, timestamps, units, quality status, schema version and lineage."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .enums import AssetClass, DataQualityStatus
from .ids import InstrumentId, MarketId, VenueId
from .money import Quantity
from .time import Instant


@dataclass(frozen=True)
class TradingSession:
    """
    A trading session within a market.
    Per MARKET_DOMAIN.md: "Session" entity.
    """

    name: str
    start_time: str  # ISO time string, e.g., "09:30:00"
    end_time: str  # ISO time string, e.g., "16:00:00"
    timezone: str  # IANA timezone, e.g., "America/New_York"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Trading session name cannot be empty")
        if not self.start_time or not self.end_time:
            raise ValueError("Trading session start and end times are required")
        if not self.timezone:
            raise ValueError("Trading session timezone is required")


@dataclass(frozen=True)
class MarketCalendar:
    """
    Market calendar with sessions and holidays.
    Per docs/05_data_market/06_MARKET_CALENDAR.md:
    "Market timezone, sessions, holidays, maintenance and exceptional closures."
    """

    market_id: MarketId
    timezone: str
    regular_sessions: List[TradingSession] = field(default_factory=list)
    holidays: List[str] = field(default_factory=list)  # ISO date strings
    maintenance_windows: List[Dict[str, str]] = field(default_factory=list)
    exceptional_closures: List[str] = field(default_factory=list)  # ISO date strings

    def is_trading_day(self, date_str: str) -> bool:
        """Check if a given date (ISO format) is a trading day."""
        return date_str not in self.holidays and date_str not in self.exceptional_closures


@dataclass(frozen=True)
class ContractSpec:
    """
    Contract specification for an instrument.
    Per MARKET_DOMAIN.md: "ContractSpec" entity.
    """

    contract_size: Quantity
    tick_size: Quantity
    tick_value: Quantity
    quote_currency: str
    underlying_asset: Optional[str] = None
    expiry: Optional[str] = None  # ISO date string for derivatives
    strike: Optional[Quantity] = None  # For options

    def __post_init__(self) -> None:
        if self.tick_size.value <= 0:
            raise ValueError("Tick size must be positive")
        if self.contract_size.value <= 0:
            raise ValueError("Contract size must be positive")


@dataclass(frozen=True)
class Instrument:
    """
    Canonical financial instrument.
    Per MARKET_DOMAIN.md: "Canonical identifiers, precision, trading hours and market-specific rules are authoritative."
    Per DATABASE_CANONICAL_MODEL.md: "Instrument, InstrumentVersion" entities.
    """

    instrument_id: InstrumentId
    symbol: str
    display_name: str
    asset_class: AssetClass
    precision: int  # Decimal places for quantity
    market_id: MarketId
    venue_ids: List[VenueId]
    contract_spec: ContractSpec
    calendar: MarketCalendar
    status: str = "ACTIVE"  # ACTIVE, SUSPENDED, DELISTED, HALTED
    created_at: Instant = field(default_factory=Instant.now)
    version: int = 1

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("Instrument symbol cannot be empty")
        if not self.display_name:
            raise ValueError("Instrument display name cannot be empty")
        if self.precision < 0:
            raise ValueError("Precision must be non-negative")
        if not self.venue_ids:
            raise ValueError("Instrument must have at least one venue")

    def validate_quantity(self, qty: Quantity) -> bool:
        """Validate that a quantity respects this instrument's precision."""
        return qty.scale == self.precision

    def validate_price(self, price: Quantity) -> bool:
        """Validate that a price respects this instrument's tick size."""
        tick_size = self.contract_spec.tick_size
        if price.value % tick_size.value != 0:
            return False
        return True

    def is_trading_session(self, now: Instant) -> bool:
        """Check if the market is currently in a trading session."""
        # Simplified: check if date is a trading day
        # Full implementation would check session times
        return self.status == "ACTIVE"


@dataclass(frozen=True)
class InstrumentVersion:
    """
    Immutable versioned reference to an instrument.
    Per DATABASE_CANONICAL_MODEL.md: "InstrumentVersion" entity.
    Per AD-010: "Live strategy/model/prompt/config references are content-addressed and immutable during deployment."
    """

    instrument_id: InstrumentId
    version: int
    effective_from: Instant
    instrument: Instrument = field(repr=False)
    effective_to: Optional[Instant] = None

    def is_active(self, at_time: Instant) -> bool:
        """Check if this version is active at the given time."""
        if at_time < self.effective_from:
            return False
        if self.effective_to is not None and at_time >= self.effective_to:
            return False
        return True


@dataclass(frozen=True)
class InstrumentMetadata:
    """
    Metadata for data contracts.
    Per DATA_CONTRACTS.md: "Required metadata: Source, symbol/instrument, timestamps, units, quality status, schema version and lineage."
    """

    instrument_id: InstrumentId
    source: str
    symbol: str
    timestamp: Instant
    units: str
    quality_status: DataQualityStatus
    schema_version: str
    lineage: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("Source is required")
        if not self.symbol:
            raise ValueError("Symbol is required")
        if not self.units:
            raise ValueError("Units are required")


__all__ = [
    "TradingSession",
    "MarketCalendar",
    "ContractSpec",
    "Instrument",
    "InstrumentVersion",
    "InstrumentMetadata",
]
