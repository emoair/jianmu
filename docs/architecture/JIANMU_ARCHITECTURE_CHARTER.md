# JianMu Architecture Charter

## Boundary-as-Data-Contract

Boundary is defined by dataset schema, support_status, expected_action, audit, compiler validation, and versioned records.

Boundary must not be implemented as scattered runtime hardcoded gates in candidate generation, routing, or free inference.

Runtime systems may read approved profile/config/state, but must not silently introduce new capability boundaries outside data contracts.

RedQueen adjusts curriculum distribution.
HydraBudget adjusts shadow budget allocation.
IronJudge verifies compiled outputs.
None of them may redefine supported capability boundaries without dataset migration and audit.

## No Runtime Keyword Rejection

No keyword-based rejection gates may be added to improve metrics.

## Evaluation, Not Interference

Regression Dashboard, boundary checks, and OOD checks are offline evaluation and readiness gates. They are not training-time hard interceptors.

## Capability Migration Path

New capability migration must go through:
dataset schema -> audit -> compiler validation -> experimental records -> readiness -> later promotion.
