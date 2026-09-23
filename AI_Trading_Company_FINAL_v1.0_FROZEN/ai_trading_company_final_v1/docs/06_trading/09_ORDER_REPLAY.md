# Order Replay

> Status: Baseline V1 — subject to final architecture audit.

## Purpose
Reconstruct order behavior.

## Purpose

Replay events for debugging, audit and recovery without resubmitting orders.

## Safety

Replay is non-mutating unless explicitly executed in a test environment.
