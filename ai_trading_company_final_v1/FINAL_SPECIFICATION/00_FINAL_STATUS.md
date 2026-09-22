# FINAL STATUS — AI-Native Proprietary Trading Company

Status: **FINAL SPECIFICATION v1.0 — ARCHITECTURE FROZEN**
Date: 2026-09-22

This package is the authoritative specification for implementation. The earlier baseline documents remain as historical/contextual material; where any conflict exists, the Final Specification and the rules below take precedence.

## Scope
Personal-use AI-native proprietary trading system, company-ready by architecture, supporting Crypto, Forex, Stocks and Commodities. V1 excludes SaaS, multi-tenancy, billing, customer accounts, public strategy marketplace and social trading.

## Non-negotiable authority chain
AI proposes → Risk Engine authorizes/vetoes → OMS accepts only valid risk-bound intents → Execution Adapter executes only OMS instructions → Reconciliation verifies broker/exchange state → Portfolio derives state from verified fills → Performance records outcomes → Research learns only from governed historical artifacts.

No AI agent, UI, Telegram command, broker adapter, or model may bypass this chain.

## Live boundary
Live is a separate environment with separate credentials, deployment, data policies, approvals and operational controls. A live strategy is an immutable approved artifact plus immutable configuration references.

## Freeze rule
Any change to risk, order semantics, execution behavior, promotion gates, credential access, or live configuration requires a versioned change proposal, automated tests, review, approval, migration plan where applicable, and a new release.
