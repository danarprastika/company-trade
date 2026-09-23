# Kilo Code Handoff — Final / Frozen

Kilo Code is the implementation and verification executor. It is not the authority for changing architecture or silently resolving specification contradictions.

## Mandatory reading order
1. `FINAL_SPECIFICATION/00_FINAL_STATUS.md`
2. `FINAL_SPECIFICATION/01_ARCHITECTURE_DECISIONS.md`
3. `FINAL_SPECIFICATION/02_RUNTIME_CONTRACTS.md`
4. `FINAL_SPECIFICATION/03_STATE_MACHINES.md`
5. `FINAL_SPECIFICATION/04_EVENT_CATALOG.md`
6. `FINAL_SPECIFICATION/05_DATABASE_CANONICAL_MODEL.md`
7. `FINAL_SPECIFICATION/06_RISK_AND_LIVE_GATE.md`
8. `FINAL_SPECIFICATION/07_SELF_IMPROVEMENT_GOVERNANCE.md`
9. `FINAL_SPECIFICATION/08_AI_AGENT_GOVERNANCE.md`
10. `FINAL_SPECIFICATION/09_SECURITY_MODEL.md`
11. `FINAL_SPECIFICATION/10_OBSERVABILITY_AND_FAILURES.md`
12. `FINAL_SPECIFICATION/11_IMPLEMENTATION_GATES.md`
13. `FINAL_SPECIFICATION/12_TRACEABILITY_AND_AUDIT.md`

## Execution workflow
Plan one gate → implement only approved scope → run tests → perform security/trading review → produce evidence → stop → await independent audit/approval.

## Prohibited behavior
- no live broker connectivity before the relevant gates
- no bypass of Risk Engine, OMS or Reconciliation
- no direct mutation of portfolio/accounting state outside governed paths
- no self-promotion by runtime agents
- no hidden credentials or undocumented environment access
- no architecture change disguised as refactoring
- no silent interpretation of contradictions

## Contradiction protocol
Stop the affected gate. Record the conflict, affected artifacts, proposed resolution, tests and migration/rollback impact in a Change Request. Implementation resumes only after the change is approved and the normative documents are updated.
