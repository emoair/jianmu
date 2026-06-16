# Controlled Opt-in Longhaul Validation

## 1. What This Version Does

v1.0.7.1 runs an 8-hour longhaul validation of the staged opt-in profile candidate.

It validates explicit opt-in behavior, default blocking, rollback stability, replayability, trace cleanliness, and compiler correctness under longer wall-clock stress.

## 2. What This Version Does Not Do

This version does not claim production function support completed, production array support completed, production recursion support completed, production readiness, official release, formal Turing completeness proven, solved program synthesis, natural language layer completed, or arbitrary project parsing completed.

## 3. Reuse Policy

This longhaul validation reuses the v1.0.7 staged opt-in profile, v1.0.6 dry-run adapter, and v1.0.5.x ExtendedIR / ExtendedEmitterC / AtomicSynthesis bridge.

It does not rewrite the adapter, bypass ExtendedIR, bypass ExtendedEmitterC, or directly use a template renderer as the final compile path.

## 4. Exit Criteria

If clean, this version may output:

`ready_for_controlled_opt_in_support_candidate_review = true`

It must not output `production_ready = true`, `production_support_completed = true`, or `official_release_ready = true`.
