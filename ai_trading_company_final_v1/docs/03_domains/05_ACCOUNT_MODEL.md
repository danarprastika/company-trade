# Account Model

> Status: Baseline V1 — subject to final architecture audit.

## Purpose
Represent trading accounts and external venue relationships.

## Isolation

Demo and live accounts are separate identities and credentials.

## Reconciliation

External account state is periodically and event-driven reconciled.
