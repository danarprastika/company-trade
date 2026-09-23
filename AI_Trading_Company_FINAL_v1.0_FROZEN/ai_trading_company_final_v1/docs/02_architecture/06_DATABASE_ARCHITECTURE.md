# Database Architecture

> Status: Baseline V1 — subject to final architecture audit.

## Purpose
Define persistence strategy without prematurely locking implementation technology.

## Data classes

Operational state, immutable evidence, analytical datasets, event history, audit ledger and caches.

## Consistency

Trading/accounting mutations use transactional boundaries. Analytical workloads must not corrupt operational state.

## Migration

Schema changes are versioned, tested and recoverable.
