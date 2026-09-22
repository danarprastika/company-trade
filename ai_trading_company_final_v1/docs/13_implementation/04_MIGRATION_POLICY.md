# Migration Policy

> Status: Baseline V1 — subject to final architecture audit.

## Purpose
Move safely between architectural versions.

## Rule

Never silently rewrite historical trading evidence.

## Process

Introduce compatibility layer → migrate → validate → remove old path only after evidence.
