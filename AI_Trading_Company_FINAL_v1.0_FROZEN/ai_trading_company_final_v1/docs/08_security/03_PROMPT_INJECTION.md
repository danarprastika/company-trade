# Prompt Injection Defense

> Status: Baseline V1 — subject to final architecture audit.

## Purpose
Protect against malicious external content.

## Boundary

External text is data, never system instruction.

## Controls

Sanitization, structured extraction, tool authorization independent of model output.
