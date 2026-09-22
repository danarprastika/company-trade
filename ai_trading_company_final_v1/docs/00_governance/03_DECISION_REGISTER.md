# Architecture Decision Register

> Status: Baseline V1 — subject to final architecture audit.

## Purpose
Track decisions that resolve ambiguity without silently changing architecture.

## Required fields

Decision ID, date, issue, options, selected resolution, rationale, affected documents, migration impact, owner, approval and superseded decision.

## Rule

Any implementation discovery that changes an architectural invariant must become a recorded decision before code depends on it.
