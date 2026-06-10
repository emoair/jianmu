# Production Profile Dry-run Candidate

## 1. What This Version Does

v1.0.6 creates a shadow production-profile dry-run candidate for the experimental FunctionIR / ArrayIR / FunctionArrayIR / StructuredRecursion bridge.

It validates whether the bridge can operate under production-like profile constraints without modifying the default profile or enabling real promotion.

## 2. What This Version Does Not Do

This version does not claim:

- production function support completed
- production array support completed
- production recursion support completed
- production readiness
- formal Turing completeness proven
- solved program synthesis
- natural language layer completed
- arbitrary project parsing completed

## 3. Dry-run Principle

Dry-run means:

- the profile exists only as explicit opt-in shadow config
- default runtime path remains unchanged
- no user-facing production enablement
- no real promotion
- no release
- no tag
- all outputs are audit records and traces

## 4. Exit Criteria

If dry-run is clean, this version may output:

`ready_for_controlled_profile_review = true`

It must not output:

`production_ready = true`
