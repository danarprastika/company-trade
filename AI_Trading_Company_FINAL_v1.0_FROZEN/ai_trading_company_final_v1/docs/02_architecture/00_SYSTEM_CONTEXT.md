# System Context

> Status: Baseline V1 — subject to final architecture audit.

## Purpose
Define external actors and boundaries.

## Actors

Owner, Master AI, runtime AI employees, Web/App, Telegram, market-data providers, news providers, brokers/exchanges, model providers, infrastructure and storage.

## Boundary

External systems are untrusted and isolated behind adapters. Live broker access exists only through governed execution paths.
