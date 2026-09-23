# Source of Truth and Change Control — Final / Frozen

## Authority
`FINAL_SPECIFICATION/` is the sole normative specification layer. Supporting documentation exists to make implementation understandable and operationally usable; it must remain semantically consistent with the canonical layer.

## Conflict resolution
- Final Specification vs supporting doc: Final Specification wins; supporting doc must be corrected.
- Supporting docs conflict: use governance/document-index priority and record the resolution.
- Code conflicts with specification: code is incorrect until the specification is formally changed.
- Test conflicts with specification: determine whether the test or specification is wrong; do not weaken the contract merely to make tests pass.

## Change classes
- C0 Editorial: no semantic change.
- C1 Non-critical implementation clarification: does not change authority, security, state, event or trading semantics.
- C2 Contract change: changes API/domain/event/state/database semantics; requires affected-gate review.
- C3 Safety-critical change: risk, execution, credentials, live gate, promotion, security or environment isolation; requires full impact analysis and explicit approval.

## Required Change Request fields
ID, reason, affected documents, affected contracts, affected states/events/entities, security impact, trading impact, migration plan, rollback plan, tests, evidence, approvers, release/version.
