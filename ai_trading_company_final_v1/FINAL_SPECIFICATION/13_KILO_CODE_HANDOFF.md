# Kilo Code Handoff — Final

Kilo Code must treat `/FINAL_SPECIFICATION/` as the highest-priority project specification. Existing baseline docs are supporting references.

Required workflow: read project identity → read final status → read architecture decisions → read runtime contracts/state machines → plan one gate → implement → test → security review → trading review → update traceability → request approval for next gate.

Never implement live broker connectivity before G8/G9 evidence exists. Never bypass Risk Engine, OMS or reconciliation. Never give runtime agents unrestricted shell, network, credential or live-execution access.

Any contradiction discovered during coding must stop the affected gate and create a documented change request; do not silently reinterpret the specification.
