# Runtime Architecture

> Status: Baseline V1 — subject to final architecture audit.

## Purpose
Define runtime dependencies and critical paths.

## Critical path

Market event → normalized state → signal → risk → OMS → execution → fill → reconciliation.

## Control path

Owner/Web/Telegram → governed command service → authorization → task/control action → audit.

## Research path

Data snapshot → experiment → evaluation → immutable evidence → promotion request.
