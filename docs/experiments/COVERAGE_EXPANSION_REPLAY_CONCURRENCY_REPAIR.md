# Coverage Expansion and Replay Concurrency Repair

## 1. Why this version exists

v1.0.7.1 longhaul was clean, but coverage expansion did not succeed: unique compile unit and source sha256 coverage stayed at 9,896. Replay also had a 16-worker timeout and was rerun with a single worker.

This version repairs coverage breadth and replay concurrency without changing the capability boundary.

## 2. What this version does

- expands validation shape pool
- increases unique compile units
- increases source sha256 diversity
- repairs replay concurrency
- validates 16-worker replay
- runs 4-hour validation
- preserves staged opt-in boundary
- preserves default blocking
- preserves rollback
- preserves trace replayability

## 3. What this version does not do

It does not claim production function support completed, production array support completed, production recursion support completed, production readiness, official release, formal Turing completeness, solved program synthesis, natural language completion, or arbitrary project parsing.

## 4. Reuse policy

This repair reuses the v1.0.7 staged opt-in profile, v1.0.6 dry-run adapter, and v1.0.5.x ExtendedIR / ExtendedEmitterC / AtomicSynthesis bridge.

It does not rewrite the adapter, bypass ExtendedIR, bypass ExtendedEmitterC, or use a template renderer as the final compile path.
