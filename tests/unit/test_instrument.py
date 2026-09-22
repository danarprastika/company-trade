"""
G1.4 — Unit tests for Instrument Model

Tests:
- Instrument creation and validation
- ContractSpec validation
- MarketCalendar operations
- InstrumentVersion immutability
- InstrumentMetadata validation
"""

import pytest
from src.domain.instrument import (
    Instrument,
    InstrumentVersion,
    InstrumentMetadata,
    ContractSpec,
    MarketCalendar,
    TradingSession,
)
from src.domain.enums import AssetClass, DataQualityStatus
from src.domain.ids import InstrumentId, MarketId, VenueId
from src.domain.money import Quantity
from src.domain.time import Instant
from decimal import Decimal


class TestTradingSession:
    def test_creation(self):
        """TradingSession should be created with all fields."""
        session = TradingSession(
            name="RTH",
            start_time="09:30:00",
            end_time="16:00:00",
            timezone="America/New_York",
        )
        assert session.name == "RTH"
        assert session.start_time == "09:30:00"
        assert session.end_time == "16:00:00"
        assert session.timezone == "America/New_York"

    def test_empty_name_rejected(self):
        """Empty session name should be rejected."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            TradingSession(
                name="",
                start_time="09:30:00",
                end_time="16:00:00",
                timezone="America/New_York",
            )

    def test_empty_times_rejected(self):
        """Empty start/end times should be rejected."""
        with pytest.raises(ValueError, match="start and end times"):
            TradingSession(
                name="RTH",
                start_time="",
                end_time="16:00:00",
                timezone="America/New_York",
            )


class TestMarketCalendar:
    def test_creation(self):
        """MarketCalendar should be created with all fields."""
        market_id = MarketId.generate()
        session = TradingSession(
            name="RTH",
            start_time="09:30:00",
            end_time="16:00:00",
            timezone="America/New_York",
        )
        calendar = MarketCalendar(
            market_id=market_id,
            timezone="America/New_York",
            regular_sessions=[session],
            holidays=["2024-01-01"],
        )
        assert calendar.market_id == market_id
        assert calendar.timezone == "America/New_York"
        assert len(calendar.regular_sessions) == 1
        assert "2024-01-01" in calendar.holidays

    def test_is_trading_day(self):
        """is_trading_day should return False for holidays."""
        market_id = MarketId.generate()
        calendar = MarketCalendar(
            market_id=market_id,
            timezone="America/New_York",
            holidays=["2024-01-01"],
            exceptional_closures=["2024-07-04"],
        )
        assert calendar.is_trading_day("2024-01-01") is False
        assert calendar.is_trading_day("2024-07-04") is False
        assert calendar.is_trading_day("2024-06-15") is True


class TestContractSpec:
    def test_creation(self):
        """ContractSpec should be created with all fields."""
        spec = ContractSpec(
            contract_size=Quantity.from_string("100", scale=0),
            tick_size=Quantity.from_string("0.01", scale=2),
            tick_value=Quantity.from_string("1.00", scale=2),
            quote_currency="USD",
        )
        assert spec.contract_size.value == Decimal("100")
        assert spec.tick_size.value == Decimal("0.01")
        assert spec.quote_currency == "USD"

    def test_zero_tick_size_rejected(self):
        """Zero tick size should be rejected."""
        with pytest.raises(ValueError, match="Tick size must be positive"):
            ContractSpec(
                contract_size=Quantity.from_string("100", scale=0),
                tick_size=Quantity.from_string("0", scale=2),
                tick_value=Quantity.from_string("1.00", scale=2),
                quote_currency="USD",
            )

    def test_zero_contract_size_rejected(self):
        """Zero contract size should be rejected."""
        with pytest.raises(ValueError, match="Contract size must be positive"):
            ContractSpec(
                contract_size=Quantity.from_string("0", scale=0),
                tick_size=Quantity.from_string("0.01", scale=2),
                tick_value=Quantity.from_string("1.00", scale=2),
                quote_currency="USD",
            )


class TestInstrument:
    def _make_contract_spec(self) -> ContractSpec:
        return ContractSpec(
            contract_size=Quantity.from_string("100", scale=0),
            tick_size=Quantity.from_string("0.01", scale=2),
            tick_value=Quantity.from_string("1.00", scale=2),
            quote_currency="USD",
        )

    def _make_calendar(self) -> MarketCalendar:
        return MarketCalendar(
            market_id=MarketId.generate(),
            timezone="America/New_York",
            regular_sessions=[
                TradingSession(
                    name="RTH",
                    start_time="09:30:00",
                    end_time="16:00:00",
                    timezone="America/New_York",
                )
            ],
        )

    def _make_instrument(self, **kwargs) -> Instrument:
        defaults = dict(
            instrument_id=InstrumentId.generate(),
            symbol="AAPL",
            display_name="Apple Inc.",
            asset_class=AssetClass.STOCK,
            precision=0,
            market_id=MarketId.generate(),
            venue_ids=[VenueId.generate()],
            contract_spec=self._make_contract_spec(),
            calendar=self._make_calendar(),
        )
        defaults.update(kwargs)
        return Instrument(**defaults)

    def test_creation(self):
        """Instrument should be created with all fields."""
        instrument = self._make_instrument()
        assert instrument.symbol == "AAPL"
        assert instrument.display_name == "Apple Inc."
        assert instrument.asset_class == AssetClass.STOCK
        assert instrument.precision == 0
        assert instrument.status == "ACTIVE"
        assert instrument.version == 1

    def test_empty_symbol_rejected(self):
        """Empty symbol should be rejected."""
        with pytest.raises(ValueError, match="symbol cannot be empty"):
            self._make_instrument(symbol="")

    def test_empty_display_name_rejected(self):
        """Empty display name should be rejected."""
        with pytest.raises(ValueError, match="display name cannot be empty"):
            self._make_instrument(display_name="")

    def test_negative_precision_rejected(self):
        """Negative precision should be rejected."""
        with pytest.raises(ValueError, match="Precision must be non-negative"):
            self._make_instrument(precision=-1)

    def test_no_venues_rejected(self):
        """Empty venue list should be rejected."""
        with pytest.raises(ValueError, match="at least one venue"):
            self._make_instrument(venue_ids=[])

    def test_validate_quantity_correct_scale(self):
        """validate_quantity should return True for correct scale."""
        instrument = self._make_instrument(precision=2)
        qty = Quantity.from_string("100.50", scale=2)
        assert instrument.validate_quantity(qty) is True

    def test_validate_quantity_wrong_scale(self):
        """validate_quantity should return False for wrong scale."""
        instrument = self._make_instrument(precision=2)
        qty = Quantity.from_string("100", scale=0)
        assert instrument.validate_quantity(qty) is False

    def test_validate_price_correct_tick(self):
        """validate_price should return True for valid tick."""
        instrument = self._make_instrument()
        price = Quantity.from_string("150.01", scale=2)
        assert instrument.validate_price(price) is True

    def test_validate_price_wrong_tick(self):
        """validate_price should return False for invalid tick."""
        instrument = self._make_instrument()
        price = Quantity.from_string("150.005", scale=3)
        assert instrument.validate_price(price) is False

    def test_is_trading_session_active(self):
        """is_trading_session should return True for ACTIVE status."""
        instrument = self._make_instrument(status="ACTIVE")
        assert instrument.is_trading_session(Instant.now()) is True

    def test_is_trading_session_inactive(self):
        """is_trading_session should return False for non-ACTIVE status."""
        instrument = self._make_instrument(status="SUSPENDED")
        assert instrument.is_trading_session(Instant.now()) is False


class TestInstrumentVersion:
    def test_creation(self):
        """InstrumentVersion should be created with all fields."""
        instrument = Instrument(
            instrument_id=InstrumentId.generate(),
            symbol="AAPL",
            display_name="Apple Inc.",
            asset_class=AssetClass.STOCK,
            precision=0,
            market_id=MarketId.generate(),
            venue_ids=[VenueId.generate()],
            contract_spec=ContractSpec(
                contract_size=Quantity.from_string("100", scale=0),
                tick_size=Quantity.from_string("0.01", scale=2),
                tick_value=Quantity.from_string("1.00", scale=2),
                quote_currency="USD",
            ),
            calendar=MarketCalendar(
                market_id=MarketId.generate(),
                timezone="America/New_York",
            ),
        )
        version = InstrumentVersion(
            instrument_id=instrument.instrument_id,
            version=1,
            effective_from=Instant.now(),
            instrument=instrument,
        )
        assert version.version == 1
        assert version.effective_to is None

    def test_is_active(self):
        """is_active should return True within effective period."""
        instrument = Instrument(
            instrument_id=InstrumentId.generate(),
            symbol="AAPL",
            display_name="Apple Inc.",
            asset_class=AssetClass.STOCK,
            precision=0,
            market_id=MarketId.generate(),
            venue_ids=[VenueId.generate()],
            contract_spec=ContractSpec(
                contract_size=Quantity.from_string("100", scale=0),
                tick_size=Quantity.from_string("0.01", scale=2),
                tick_value=Quantity.from_string("1.00", scale=2),
                quote_currency="USD",
            ),
            calendar=MarketCalendar(
                market_id=MarketId.generate(),
                timezone="America/New_York",
            ),
        )
        now = Instant.now()
        version = InstrumentVersion(
            instrument_id=instrument.instrument_id,
            version=1,
            effective_from=now,
            instrument=instrument,
        )
        assert version.is_active(now) is True

    def test_is_active_before_effective(self):
        """is_active should return False before effective_from."""
        instrument = Instrument(
            instrument_id=InstrumentId.generate(),
            symbol="AAPL",
            display_name="Apple Inc.",
            asset_class=AssetClass.STOCK,
            precision=0,
            market_id=MarketId.generate(),
            venue_ids=[VenueId.generate()],
            contract_spec=ContractSpec(
                contract_size=Quantity.from_string("100", scale=0),
                tick_size=Quantity.from_string("0.01", scale=2),
                tick_value=Quantity.from_string("1.00", scale=2),
                quote_currency="USD",
            ),
            calendar=MarketCalendar(
                market_id=MarketId.generate(),
                timezone="America/New_York",
            ),
        )
        now = Instant.now()
        future = Instant.from_unix_seconds(now.unix_seconds + 100)
        version = InstrumentVersion(
            instrument_id=instrument.instrument_id,
            version=1,
            effective_from=future,
            instrument=instrument,
        )
        assert version.is_active(now) is False


class TestInstrumentMetadata:
    def test_creation(self):
        """InstrumentMetadata should be created with all fields."""
        metadata = InstrumentMetadata(
            instrument_id=InstrumentId.generate(),
            source="polygon.io",
            symbol="AAPL",
            timestamp=Instant.now(),
            units="USD",
            quality_status=DataQualityStatus.VALID,
            schema_version="1.0.0",
            lineage=["raw", "normalized"],
        )
        assert metadata.source == "polygon.io"
        assert metadata.symbol == "AAPL"
        assert metadata.quality_status == DataQualityStatus.VALID
        assert metadata.lineage == ["raw", "normalized"]

    def test_empty_source_rejected(self):
        """Empty source should be rejected."""
        with pytest.raises(ValueError, match="Source is required"):
            InstrumentMetadata(
                instrument_id=InstrumentId.generate(),
                source="",
                symbol="AAPL",
                timestamp=Instant.now(),
                units="USD",
                quality_status=DataQualityStatus.VALID,
                schema_version="1.0.0",
            )

    def test_empty_symbol_rejected(self):
        """Empty symbol should be rejected."""
        with pytest.raises(ValueError, match="Symbol is required"):
            InstrumentMetadata(
                instrument_id=InstrumentId.generate(),
                source="polygon.io",
                symbol="",
                timestamp=Instant.now(),
                units="USD",
                quality_status=DataQualityStatus.VALID,
                schema_version="1.0.0",
            )

    def test_empty_units_rejected(self):
        """Empty units should be rejected."""
        with pytest.raises(ValueError, match="Units are required"):
            InstrumentMetadata(
                instrument_id=InstrumentId.generate(),
                source="polygon.io",
                symbol="AAPL",
                timestamp=Instant.now(),
                units="",
                quality_status=DataQualityStatus.VALID,
                schema_version="1.0.0",
            )
