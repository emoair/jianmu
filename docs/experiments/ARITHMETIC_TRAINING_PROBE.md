# v0.9.3 Arithmetic Training Probe

## 1. Why v0.9.3 Exists

v0.9.2 generated audited arithmetic curriculum data but did not train a model. v0.9.3 tests whether JianMu shows a bounded improvement signal for supported arithmetic routing under no-label free-beam evaluation.

## 2. What Is Tested

The probe checks supported arithmetic retention, heldout supported arithmetic success, precedence, parentheses, unary minus, exact division, division-by-zero rejection, non-integer division rejection/quarantine, trap rejection, future/near-OOD isolation/quarantine, forbidden-field guard behavior, full_router_root state capture/reload, workload counters, and compiler-backed spot audit status.

## 3. Non-Claims

This probe does not claim solved arithmetic, stable convergence, solved OOD, general program synthesis, same-size LLM advantage, safe real promotion, or production readiness.
