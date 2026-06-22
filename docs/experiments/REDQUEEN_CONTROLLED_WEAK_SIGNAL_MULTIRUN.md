# RedQueen Controlled Weak Signal Multirun

## 1. What this version does

v1.0.8.5 runs a 6-hour multi-round RedQueen governance validation with controlled weak signal injection in a shadow governance metrics lane.

It tests whether RedQueen responds to weak signals by increasing review, increasing sample push, lowering difficulty, and later annealing after the weak signal is removed.

## 2. What this version does not do

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
- autonomous governance completed
- model training completed
- real compiler weakness detected
- real compiler weakness fixed

## 3. Two-lane honesty rule

Real compile lane:

- real compiler correctness remains source of truth
- synthetic weak signal must not count as compiler failure
- real compiler correctness must remain separately reported

Shadow governance lane:

- may inject synthetic weak signal
- must mark `weak_signal_is_synthetic = true`
- must mark `weak_signal_affects_real_correctness = false`
- may influence RedQueen scheduling
- cannot influence production claims

## 4. Exit criteria

If this version passes, it may only output:

`redqueen_controlled_weak_signal_response_positive = true`

It must not output:

- `production_ready = true`
- `production_support_completed = true`
- `official_release_ready = true`
- `autonomous_governance_completed = true`
