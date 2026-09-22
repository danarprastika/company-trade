# Event Architecture

> Status: Baseline V1 — subject to final architecture audit.

## Purpose
Define event-driven foundations.

## Event classes

MarketDataReceived, MarketStateChanged, NewsEventReceived, SignalCreated, RiskDecisionMade, OrderIntentApproved, OrderSubmitted, OrderAcknowledged, FillReceived, ReconciliationChanged, PositionChanged, KillSwitchActivated, DeploymentChanged and IncidentRaised.

## Envelope

event_id, event_type, schema_version, occurred_at, produced_at, source, correlation_id, causation_id, aggregate_id, payload_hash.

## Rule

Events are immutable facts. Commands request actions; events report facts.
