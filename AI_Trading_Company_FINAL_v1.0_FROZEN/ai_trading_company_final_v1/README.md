# AI Trading Company — Final Frozen Specification v1.0

This repository is the normative architecture/specification baseline for a personal-use, AI-native proprietary trading system designed to be company-ready by architecture.

## Source of truth
`FINAL_SPECIFICATION/` is normative. Supporting `docs/`, `.kilocode/` and audit artifacts are subordinate and must remain synchronized.

## Core safety boundary
AI proposes → Risk authorizes/vetoes → OMS governs → Execution executes → Reconciliation verifies → Portfolio derives state → Performance records → Research learns. No bypass path is permitted.

## Markets
Crypto, Forex, Stocks and Commodities are independently governed market modules.

## Implementation
Implementation starts at G1 only after this frozen G0 baseline. Kilo Code implements one gate at a time; independent review determines gate readiness. Live activation is not implied by documentation completion.

See `FINAL_SPECIFICATION/19_FINALIZATION_AUDIT.md` for the finalization record.
