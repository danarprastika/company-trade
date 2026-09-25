# IMPLEMENTATION CONSTITUTION
## FINAL / FROZEN IMPLEMENTATION BASELINE v1.0

Status: NORMATIVE
Authority: FINAL_SPECIFICATION
Applies: G1–G11
Purpose: Prevent implementation drift after architecture freeze.

## 1. Constitutional Rule

The repository is no longer an architecture-design workspace. It is an implementation workspace.

Kilo Code MUST implement the frozen architecture and MUST NOT redesign it during normal gate execution.

The implementation objective is:
> make the documented system real, testable, observable, secure, deterministic where required, and evidence-backed.

## 2. Source-of-Truth Hierarchy

Highest to lowest:

1. FINAL_SPECIFICATION/
2. This constitution and the implementation-control documents in FINAL_SPECIFICATION/
3. Supporting docs/ and .kilocode/ material
4. Existing implementation artifacts
5. General engineering conventions

If two lower-level sources conflict with a higher-level source, the higher-level source wins.

## 3. Non-Negotiable Boundaries

Kilo Code MUST NOT:
- redefine authority ownership;
- create a second Risk authority;
- allow AI to bypass Risk;
- allow AI to authorize itself for live trading;
- connect live brokers before the applicable gates;
- weaken fail-closed behavior;
- treat Signal as Order;
- treat proposed AI output as execution authority;
- mutate append-only audit/decision records;
- silently change canonical event names;
- silently change state-machine transitions;
- silently change canonical database semantics;
- introduce look-ahead into research/backtesting;
- reuse live credentials in research/demo environments;
- collapse isolated markets into an uncontrolled shared trading domain.

## 4. Engineering Freedom

Kilo Code MAY choose implementation details when the specification intentionally leaves them open, provided that:
- behavior remains contract-compatible;
- security and isolation requirements are preserved;
- tests prove the chosen behavior;
- the choice is documented;
- the choice does not create a new architectural authority.

## 5. Determinism

Where the specification requires deterministic behavior, implementations MUST expose stable inputs, ordering, versioning, and reproducible outputs.

Non-deterministic infrastructure behavior MUST NOT be hidden behind a claim of deterministic business behavior.

## 6. Change Rule

Any change to frozen architecture, authority, canonical vocabulary, event identity, state transitions, risk/live gates, isolation boundaries, or normative contracts requires a Change Request.

No implementation PR, commit, or patch may silently act as an architecture decision.

## 7. Evidence Rule

A feature is not considered implemented merely because source code exists.

Every gate requires:
- implementation evidence;
- automated test evidence;
- static/type/lint evidence where applicable;
- security evidence where applicable;
- explicit mapping to the governing contract;
- recorded unresolved items, if any.

## 8. Completion Rule

A gate may be declared PASS only when its acceptance conditions and evidence standard are satisfied.

"Tests pass" alone is not a gate PASS.

## 9. Live Boundary

Implementation progress does not imply live authorization.

Live activation remains separately gated and requires all applicable prerequisites, approvals, security controls, operational controls, and human authority defined by FINAL_SPECIFICATION.

## 10. Stop Conditions

Kilo Code MUST stop and report rather than guess when:
- a normative contradiction is discovered;
- a required authority is ambiguous;
- a security boundary cannot be enforced;
- a required canonical identifier is missing;
- a test cannot establish a mandatory invariant;
- implementation would require changing a frozen contract.

The report MUST identify the exact document/section and propose a Change Request rather than silently resolving the issue.


## Long-lived production requirement
This implementation is NOT an MVP exercise. Kilo Code must implement production-capable foundations, failure paths, security, observability, upgradeability, and maintainability rather than optimizing for a demo or happy-path success.
