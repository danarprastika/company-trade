# Broker Outage Runbook

> Status: Baseline V1 — subject to final architecture audit.

## Purpose
Handle external execution outage.

## Rule

Stop new orders if required; preserve local intent state; monitor external recovery; reconcile before resume.
