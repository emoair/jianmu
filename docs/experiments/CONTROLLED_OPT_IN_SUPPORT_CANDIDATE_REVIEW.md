# Controlled Opt-in Support Candidate Review

## 1. What This Version Does

v1.0.8 reviews whether the staged opt-in profile can be promoted to a controlled opt-in support candidate.

It defines support scope, unsupported boundaries, failure handling, rollback behavior, trace requirements, and reviewer checklist for the opt-in bridge.

## 2. What This Version Does Not Do

This version does not claim production function support completed, production array support completed, production recursion support completed, production readiness, official release, formal Turing completeness, solved program synthesis, natural language completion, or arbitrary project parsing.

## 3. Support Candidate Principle

Controlled opt-in support candidate means the default profile remains unchanged, explicit opt-in is required, real promotion remains disabled, user-facing production remains disabled, support is limited to documented subsets, unsupported inputs are rejected or classified safely, every supported execution produces trace, rollback remains clean, and production support completed remains false.

## 4. Exit Criteria

If clean, the only positive readiness is `ready_for_controlled_opt_in_support_candidate = true`.

It must not set `production_ready = true`, `production_support_completed = true`, or `official_release_ready = true`.
