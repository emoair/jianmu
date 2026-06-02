# Turing Frontier Failure Taxonomy

v0.9.26.1 classifies frontier failures into loop-variant, loop-exit, update-order, nontermination, timeout-unknown, recursion base-case, recursion step, state-growth, counter-machine, WHILE-language, token-to-IR, watchdog, and compiler runtime mismatch categories.

The taxonomy is diagnostic. It can drive RedQueen repair assignments and repair dataset generation, but it does not change the production support boundary and does not turn experimental unbounded control, recursion, or state growth into current_supported features.
