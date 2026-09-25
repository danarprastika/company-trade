# AI Trading Company — Final Frozen Specification v1.0

This repository is the normative architecture/specification baseline for a personal-use, AI-native proprietary trading system designed to be company-ready by architecture.

## Source of truth
`FINAL_SPECIFICATION/` is normative. Supporting `docs/`, `.kilocode/` and audit artifacts are subordinate and must remain synchronized.

## Core safety boundary
AI proposes → Risk authorizes/vetoes → OMS governs → Execution executes → Reconciliation verifies → Portfolio derives state → Performance records → Research learns. No bypass path is permitted.

## Markets
Crypto, Forex, Stocks and Commodities are independently governed market modules.

## Implementation
G0 has been finally reconciled and is PASS. Implementation starts at G1. Kilo Code implements one gate at a time and produces evidence for each gate. Live activation is not implied by documentation completion.

See `FINAL_SPECIFICATION/19_FINALIZATION_AUDIT.md` for the finalization record.

## MAX IMPLEMENTATION CONTROL BASELINE

This package additionally contains implementation-control documents 14–24 in FINAL_SPECIFICATION.
They define the implementation constitution, G1 contract, gate execution protocol, change control,
canonical implementation mapping, evidence standard, Kilo Code entrypoint, repository/evidence guidance,
security checklist, testing strategy, and Definition of Done.

Kilo Code starts at G1. G0 is already reconciled and frozen. These documents do not authorize live trading.


## ANTI-MVP / PRODUCTION MATURITY
This baseline is explicitly not an MVP-only implementation target. FINAL_SPECIFICATION now includes
production maturity, non-functional requirements, deployment/release governance, disaster recovery,
provider/broker certification, AI model governance, data lifecycle, accounting/reconciliation assurance,
observability/SLOs, operational readiness, production certification, long-term compatibility, resilience
game days, and an anti-MVP completeness audit.

These controls do not authorize live trading by themselves. Live activation remains subject to the frozen
live gates, approvals, security, operational readiness, and human authority requirements.


## Enterprise Final Baseline
The package is frozen as the enterprise implementation baseline. Polyglot language boundaries are selective and are not treated as security-by-obscurity. Future changes require the documented Change Request process.

## Final Language Boundary
Frontend: TypeScript. Backend: Go. Safety-critical core: Rust where justified. AI/Research: Python. Persistence: SQL. Infrastructure: IaC.
