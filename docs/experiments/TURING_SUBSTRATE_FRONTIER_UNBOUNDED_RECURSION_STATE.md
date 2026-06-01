# Turing Substrate Frontier: Unbounded Control, Recursion, and State

## Why v0.9.26 Exists

The bounded JianMu substrate is strong, but a V1.0 goal framed as a Turing-complete substrate cannot be released from bounded-control evidence alone. v0.9.26 opens the experimental frontier for unbounded while, recursion, and growing/addressable state while keeping production boundaries unchanged.

## Semantic vs Validation Distinction

The semantic layer may represent unbounded while and recursion. Runtime validation remains watchdog-limited with max steps, max runtime, deterministic timeout classification, trace truncation, and safe cleanup. Finite tests do not prove Turing completeness.

## Constructive Expressivity Evidence

This version adds counter-machine and WHILE-language witness mappings with example programs, terminating witnesses, nontermination observations, timeout-unknown cases, and explicit limitations. These mappings are constructive evidence only, not formal proof.

## Nontermination Handling

The frontier records terminating_known, nonterminating_observed, timeout_unknown, unsupported, and review. Unknown-halting and nonterminating samples must not contain fake expected_output.

## RedQueen / Symbiote Role

RedQueen generates Turing-frontier curriculum assignments and required features. Symbiote probes frontier token adaptation while preserving heldout generalization and comfort-zone collapse checks. Neither changes the production boundary.

## Longhaul Hard Rule

Endurance runs require wall_clock_min_hours = 6. Early sample completion cannot end the run. If real wall-clock time is below 6 hours, endurance_completed must be false and the run must be marked partial.

## Non-Claims

No Turing completeness proven, no production support for recursion/unbounded/state growth, no arbitrary project parsing, no natural language layer completion, and no V1.0 release.
