# Shutdown Runbook

> Status: Baseline V1 — subject to final architecture audit.

## Purpose
Safely stop the system.

## Flow

Disable new trading → handle/cancel governed open orders → reconcile → persist state → stop services.
