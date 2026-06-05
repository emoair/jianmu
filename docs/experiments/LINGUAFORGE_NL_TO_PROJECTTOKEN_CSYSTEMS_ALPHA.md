# v1.1.1 LinguaForge NL-to-ProjectToken CSystems Alpha

## 1. Why LinguaForge v1.1.1

v1.0.2 to v1.0.4.1 strengthened ProjectCartographer parsing, ForgeCorpus algorithm tokens, C systems frontier evidence, and RedQueen symbol binding. v1.1.1 tests whether wider Chinese requirements can enter JianMu through a bounded natural-language adapter.

## 2. Architecture

Chinese NL -> LinguaForge NL Adapter -> ProjectToken / AlgorithmToken / CSystemsToken / SymbolBindingToken -> frozen v1.0.4.1 substrate -> IR / candidate -> compiler / watchdog validation.

## 3. NL Does Not Bypass Token

The alpha adapter must not emit C source, target_ir JSON, or compiler candidates directly. Natural language is not a truth source. It is normalized into audited token-layer structures and then validated through the frozen substrate.

## 4. Wider Natural Language Boundary

The probe covers algorithm requests, project layout requests, pointer and malloc requests, sandboxed file IO requests, multi-file split requests, struct requests, and symbol rename/refactor requests.

## 5. Alpha Longhaul Rule

The full run requires `wall_clock_min_hours >= 6`. If the wall clock is below six hours, readiness cannot be positive and must report `wall_clock_below_minimum`.

## 6. Non-Claims

This version does not claim natural language layer completion, general natural language understanding, production NL interface, arbitrary project parsing, solved program synthesis, production readiness, formal Turing completeness, or emergence.
