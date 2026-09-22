# G1 Implementation Plan — Domain Foundation

**Gate:** G1 — Domain Foundation
**Status:** PLANNED
**Based on:** `FINAL_SPECIFICATION/11_IMPLEMENTATION_GATES.md` (G1: "Domain foundation: canonical IDs, time, money, events, errors.")
**Bootstrap prompt G1:** IDs, timestamps, money, quantity, instruments, enums, errors, event envelope, correlation IDs, causation IDs, configuration, persistence, migrations.

---

## G1 Objective

Establish the canonical domain foundation: identity types, temporal semantics, monetary/quantity types, event/command envelopes, error taxonomy, configuration model, persistence layer, and migration framework. All types must be deterministic, testable, and free of live-trading capability.

---

## G1 Deliverables

| # | Deliverable | Specification Reference |
|---|-------------|------------------------|
| 1 | Canonical ID types (UUIDv7-based, typed) | `DATABASE_CANONICAL_MODEL.md` |
| 2 | Timestamp semantics (UTC, monotonic durations) | `CLOCK_SYNC.md`, `RUNTIME_CONTRACTS.md` |
| 3 | Money type (fixed-precision decimal) | `DATABASE_CANONICAL_MODEL.md` ("fixed-precision decimal semantics, never binary floating point") |
| 4 | Quantity type (fixed-precision decimal) | `DATABASE_CANONICAL_MODEL.md` |
| 5 | Instrument model (canonical identifiers, precision) | `MARKET_DOMAIN.md`, `DATABASE_CANONICAL_MODEL.md` |
| 6 | Enum definitions (status codes, reason codes, error classes) | `STATUS_CODE_CATALOG.md`, `REASON_CODE_CATALOG.md`, `ERROR_TAXONOMY.md` |
| 7 | Error taxonomy | `ERROR_TAXONOMY.md` |
| 8 | Event envelope | `RUNTIME_CONTRACTS.md` (event envelope) |
| 9 | Command envelope | `RUNTIME_CONTRACTS.md` (command envelope) |
| 10 | Correlation ID / Causation ID | `RUNTIME_CONTRACTS.md`, `OBSERVABILITY_AND_FAILURES.md` |
| 11 | Configuration model (versioned, traceable) | `CONFIGURATION_GOVERNANCE.md` |
| 12 | Persistence layer (transactional boundaries) | `DATABASE_ARCHITECTURE.md` |
| 13 | Migration framework (versioned, tested, recoverable) | `MIGRATION_POLICY.md`, `DATABASE_ARCHITECTURE.md` |

---

## G1 Task Breakdown

### Task G1.1 — Canonical ID Types
**Source:** `DATABASE_CANONICAL_MODEL.md` (entity groups reference IDs)
**Spec:** IDs must be globally unique, typed, and deterministic where needed.
**Acceptance:**
- `EntityId` type wrapping UUIDv7 (time-ordered for database locality)
- Typed ID variants: `AgentId`, `OrderId`, `StrategyId`, `InstrumentId`, `AccountId`, `PortfolioId`, `EnvironmentId`, `DeploymentId`, `ExperimentId`, `DatasetId`, `EventId`, `CommandId`, `TraceId`, `ApprovalId`, `ChangeRequestId`
- No raw string IDs in domain logic
- Unit tests for ID generation, parsing, and type safety
**Tests:** unit, contract

### Task G1.2 — Timestamp Semantics
**Source:** `CLOCK_SYNC.md`, `RUNTIME_CONTRACTS.md`
**Spec:** UTC timestamps, monotonic durations, event timestamp validation.
**Acceptance:**
- `Instant` type representing UTC timestamp with nanosecond precision
- `Duration` type using monotonic clock semantics
- Validation: timestamps must be within acceptable bounds (not future-dated beyond tolerance)
- Clock drift detection interface
**Tests:** unit, property (timestamp ordering), failure (invalid timestamps)

### Task G1.3 — Money and Quantity Types
**Source:** `DATABASE_CANONICAL_MODEL.md` ("fixed-precision decimal semantics, never binary floating point for authoritative accounting")
**Spec:** Fixed-precision decimal for all monetary and quantity calculations.
**Acceptance:**
- `Money` type with currency code and fixed-precision decimal (scale=2 for most currencies, configurable per currency)
- `Quantity` type with fixed-precision decimal (scale configurable per instrument)
- Arithmetic operations preserve precision; no silent rounding
- Comparison, addition, subtraction, multiplication, division with explicit rounding modes
- Serialization/deserialization to/from string representation
**Tests:** unit, property (precision preservation, rounding), failure (overflow)

### Task G1.4 — Instrument Model
**Source:** `MARKET_DOMAIN.md` ("Canonical identifiers, precision, trading hours and market-specific rules are authoritative.")
**Spec:** Canonical instrument identity with precision and market rules.
**Acceptance:**
- `Instrument` aggregate: `InstrumentId`, `symbol`, `displayName`, `assetClass` (Crypto/Forex/Stock/Commodity), `precision`, `tickSize`, `marketId`, `venueId`, `tradingHours`, `status`
- `InstrumentVersion` for immutable versioned references
- Validation: precision must be non-negative integer; tickSize must be positive
**Tests:** unit, contract

### Task G1.5 — Enum Definitions
**Source:** `STATUS_CODE_CATALOG.md`, `REASON_CODE_CATALOG.md`, `ERROR_TAXONOMY.md`
**Spec:** Status codes, reason codes, and error classes are stable identifiers.
**Acceptance:**
- `StatusCode` enum: DRAFT, RISK_PENDING, RISK_APPROVED, OMS_ACCEPTED, SUBMITTING, ACKNOWLEDGED, PARTIALLY_FILLED, FILLED, CANCEL_PENDING, CANCELLED, REJECTED, EXPIRED, FAILED, UNKNOWN
- `ReasonCode` enum: LIMIT, EXPOSURE, LIQUIDITY, STALE_DATA, RECONCILIATION, ENVIRONMENT, POLICY, PROVIDER, STRATEGY_STATE, SYSTEM_HEALTH
- `ErrorClass` enum: VALIDATION, AUTHORIZATION, POLICY, DATA_QUALITY, PROVIDER, NETWORK, TIMEOUT, STATE_CONFLICT, RECONCILIATION, PERSISTENCE, MODEL, SYSTEM_CRITICAL
- All enums are stable, versioned, and serializable
**Tests:** unit, contract

### Task G1.6 — Error Taxonomy
**Source:** `ERROR_TAXONOMY.md`
**Spec:** Standardized error classes with structured error types.
**Acceptance:**
- `TradingError` base type with `errorClass`, `reasonCode`, `message`, `details`
- Typed error subclasses for each error class
- Error codes are stable identifiers
- Errors carry correlation/trace IDs
**Tests:** unit, failure

### Task G1.7 — Event Envelope
**Source:** `RUNTIME_CONTRACTS.md`
**Spec:** Every event carries: event_id, aggregate_type, aggregate_id, event_type, schema_version, occurred_at_utc, recorded_at_utc, producer, correlation_id, causation_id, environment, payload_hash and sequence.
**Acceptance:**
- `EventEnvelope` type with all required fields
- `event_id`: EventId (UUIDv7)
- `aggregate_type`: string (entity type name)
- `aggregate_id`: EntityId
- `event_type`: string (versioned event name)
- `schema_version`: string (semver)
- `occurred_at_utc`: Instant
- `recorded_at_utc`: Instant
- `producer`: string (component identifier)
- `correlation_id`: TraceId
- `causation_id`: EventId or CommandId
- `environment`: EnvironmentId
- `payload_hash`: string (SHA-256)
- `sequence`: integer (monotonic per aggregate)
- Immutability: all fields are read-only after construction
**Tests:** unit, contract, property (immutability)

### Task G1.8 — Command Envelope
**Source:** `RUNTIME_CONTRACTS.md`
**Spec:** Every command carries: command_id, trace_id, actor_id, actor_type, environment, issued_at_utc, schema_version, idempotency_key, authorization_scope and payload_hash.
**Acceptance:**
- `CommandEnvelope` type with all required fields
- `command_id`: CommandId (UUIDv7)
- `trace_id`: TraceId
- `actor_id`: EntityId (AgentId or UserId)
- `actor_type`: string ("agent" or "user")
- `environment`: EnvironmentId
- `issued_at_utc`: Instant
- `schema_version`: string (semver)
- `idempotency_key`: string
- `authorization_scope`: string
- `payload_hash`: string (SHA-256)
- Immutability: all fields are read-only after construction
**Tests:** unit, contract, property (immutability)

### Task G1.9 — Correlation and Causation IDs
**Source:** `RUNTIME_CONTRACTS.md`, `OBSERVABILITY_AND_FAILURES.md`
**Spec:** Every request/task/order/event is correlated with trace_id, request_id/task_id, event_id and relevant strategy/experiment/incident identifiers.
**Acceptance:**
- `TraceId` type for request tracing
- `CausationId` type linking events to their causing command/event
- All envelopes carry correlation_id and causation_id
- Trace context propagation interface
**Tests:** unit, contract

### Task G1.10 — Configuration Model
**Source:** `CONFIGURATION_GOVERNANCE.md`
**Spec:** Configuration is versioned and traceable. No hidden environment variable may silently change live behavior.
**Acceptance:**
- `Configuration` type with version, schema, and content hash
- Configuration schema validation
- Environment-specific configuration resolution
- Configuration changes are versioned and auditable
- No live behavior changes from hidden env vars
**Tests:** unit, contract, failure (invalid configuration)

### Task G1.11 — Persistence Layer
**Source:** `DATABASE_ARCHITECTURE.md`
**Spec:** Trading/accounting mutations use transactional boundaries. Analytical workloads must not corrupt operational state.
**Acceptance:**
- Transactional write interface for domain events
- Event store with append-only semantics
- Read model projection interface
- Transactional boundary enforcement for trading mutations
- No direct database access from domain logic (repository pattern)
**Tests:** unit, integration, contract

### Task G1.12 — Migration Framework
**Source:** `MIGRATION_POLICY.md`, `DATABASE_ARCHITECTURE.md`
**Spec:** Schema changes are versioned, tested and recoverable. Never silently rewrite historical trading evidence.
**Acceptance:**
- Migration versioning system (sequential, named)
- Up/down migration support
- Migration integrity verification
- Rollback capability
- Evidence preservation (no rewriting of historical data)
**Tests:** unit, integration, failure (migration rollback)

---

## G1 Dependencies

```
G1.1 (IDs) → G1.7 (Event Envelope)
G1.1 (IDs) → G1.8 (Command Envelope)
G1.2 (Timestamps) → G1.7 (Event Envelope)
G1.2 (Timestamps) → G1.8 (Command Envelope)
G1.3 (Money/Quantity) → G1.4 (Instrument)
G1.5 (Enums) → G1.6 (Error Taxonomy)
G1.7 (Event Envelope) → G1.11 (Persistence)
G1.8 (Command Envelope) → G1.11 (Persistence)
G1.10 (Configuration) → G1.11 (Persistence)
G1.11 (Persistence) → G1.12 (Migration)
```

All G1 tasks are independent except where noted above. Tasks G1.1, G1.2, G1.3, G1.5, G1.10 can run in parallel.

---

## G1 Acceptance Criteria

1. All canonical types are defined with deterministic semantics
2. Event and command envelopes are implemented with all required fields
3. Money/quantity use fixed-precision decimal, never binary floating point
4. Idempotency keys are supported on all commands
5. Configuration is versioned and traceable
6. Persistence layer supports transactional boundaries for trading/accounting mutations
7. Migration framework is versioned, tested, and recoverable
8. Unit tests cover all type invariants
9. Contract tests verify envelope schemas
10. State-machine tests verify no impossible transitions
11. Security review confirms no credential leakage in foundation types
12. No live-trading capability is introduced (simulation-only)

---

## G1 Test Requirements

| Test Type | Scope |
|-----------|-------|
| Unit tests | All canonical types, envelopes, enums, money/quantity arithmetic |
| Contract tests | Event/command envelope schemas, serialization/deserialization |
| Property tests | Immutability, precision preservation, timestamp ordering |
| Failure tests | Invalid timestamps, overflow, invalid configuration, migration rollback |
| Security tests | No secret leakage in types, no live credential references |

---

## G1 Entry Criteria (from G0)

- G0 PASS ✓ (BOOTSTRAP_REPORT.md)
- Repository structure prepared ✓
- Source-of-truth hierarchy established ✓
- Development roles defined ✓

## G1 Exit Criteria

- All 12 tasks complete with passing tests
- Security review PASS
- No live-trading capability introduced
- Documentation synchronized with implementation
- Ready for G2 (Data/Market)

---

## Full Implementation Roadmap (G0–G11)

| Gate | Name | Key Deliverables |
|------|------|-----------------|
| G0 | Specification Integrity | BOOTSTRAP_REPORT.md, repository prepared |
| G1 | Domain Foundation | IDs, time, money, events, errors, config, persistence, migrations |
| G2 | Data/Market | Providers, quality, calendars, instruments, data contracts |
| G3 | Trading Core | Signals, intents, risk, capital, OMS, simulated execution |
| G4 | Research | Datasets, backtest, walk-forward, OOS, stress, replay |
| G5 | AI Company OS | Agent registry, tasks, tools, memory, evaluation, supervision |
| G6 | Demo/Shadow | Isolated portfolios, promotion evidence |
| G7 | Web/Telegram | Governed command path, audit |
| G8 | Broker Adapters | Sandbox/demo certification, reconciliation |
| G9 | Security/Observability/Recovery/Chaos | Secrets, observability, backup, recovery, chaos |
| G10 | Production Readiness | All tests/evidence pass, live gate approved |
| G11 | Live Gate | Explicit production approval, legal/provider eligibility |

**No gate may be skipped by changing configuration.**
