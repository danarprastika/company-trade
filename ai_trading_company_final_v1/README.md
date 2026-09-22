# AI-Native Proprietary Trading Company — Final Specification v1.0

Status: ARCHITECTURE FROZEN FOR IMPLEMENTATION

This repository is the final documentation package for a personal-use AI-native proprietary trading system designed to become company-ready. It supports Crypto, Forex, Stocks and Commodities as independently isolated market modules.

## Authoritative rule
AI proposes → Risk Engine decides/vetoes → OMS governs → Execution executes → Reconciliation verifies → Portfolio/Performance records → Research learns.

The AI company/agent swarm is an intelligence and operations layer, not a replacement for deterministic trading controls.

## Environments
Research → Test → Staging → Shadow → Demo/Paper → Live. Live is a separate production boundary with isolated credentials and approvals.

## Interfaces
Web/App is primary. Telegram is secondary and uses the exact same governed command/authorization path.

## Finalization
The architecture has been consolidated into `FINAL_SPECIFICATION/`, which is normative when conflicts exist with earlier baseline documents. Implementation is governed by `11_IMPLEMENTATION_GATES.md`.

## Important
Architecture freeze does not equal live-trading approval. Real-money activation requires successful implementation, security/trading testing, provider certification, reconciliation readiness, operational readiness, applicable legal/account eligibility and explicit production approval.
