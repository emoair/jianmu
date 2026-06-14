# Staged Opt-in Profile Candidate

## 1. What This Version Does

v1.0.7 creates an explicit staged opt-in profile candidate for the experimental FunctionIR / ArrayIR / FunctionArrayIR / StructuredRecursion bridge.

The profile is manually enabled only. It does not change the default runtime profile.

## 2. What This Version Does Not Do

This version does not claim:

- production function support completed
- production array support completed
- production recursion support completed
- production readiness
- official release
- formal Turing completeness proven
- solved program synthesis
- natural language layer completed
- arbitrary project parsing completed

## 3. Staged Opt-in Principle

- default profile remains unchanged
- explicit flag / config required
- user-facing production remains disabled
- real promotion remains disabled
- opt-in profile can be enabled and disabled safely
- every opt-in execution must generate audit trace
- rollback must restore default behavior

## 4. Exit Criteria

If clean, this version may output:

`ready_for_controlled_opt_in_support_review = true`

It must not output:

`production_ready = true`

`production_support_completed = true`

`official_release_ready = true`
