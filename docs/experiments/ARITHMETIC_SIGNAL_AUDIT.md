# v0.9.3.1 Arithmetic Signal Audit

## 1. Why Audit v0.9.3

v0.9.3 reported a strong arithmetic probe signal: candidate hit, correct output in beam, and top-1 rate improved under no-label free-beam evaluation. The values were also unusually regular, especially the 0.8 to 0.95 transition, so v0.9.3.1 audits whether the signal reflects real sample-level arithmetic improvement or a fixed harness effect.

## 2. v0.9.3 Positive Signal

The v0.9.3 records report candidate hit 0.8 to 0.95, correct output in beam 0.8 to 0.95, top-1 0.4 to 0.95, heldout supported success near 0.95, zero forbidden-field access, full_router_root state capture, and cross-process reload.

## 3. Risk of Regular 0.95 Values

Regular values can indicate a cap, threshold, index-period rule, or summary path rather than arithmetic-specific candidate-space improvement. This audit treats regularity as a claim risk that must be explained.

## 4. Internal Evaluator vs Real Compiler

v0.9.3 clearly used `internal_evaluator` for the compiler spot audit. v0.9.3.1 preserves that boundary and does not relabel internal evaluator results as real compiler verification.

## 5. What Counts as Real Arithmetic Signal

A real arithmetic signal requires per-sample candidate generation evidence, no forbidden-field leakage, heldout group separation, stage-specific arithmetic behavior, and non-fixed metric provenance.

## 6. Leakage / Summary / Fixed Gain

Leakage includes target_ir or expected_output access before candidate generation, boundary label access in free evaluation, or train/heldout group overlap. Summary-only records and fixed gain rules reduce claim strength even when aggregate metrics look strong.

## 7. Non-Claims

This audit does not prove solved arithmetic, stable convergence, solved OOD, same-size LLM advantage, safe real promotion, production readiness, or real compiler-backed arithmetic.
