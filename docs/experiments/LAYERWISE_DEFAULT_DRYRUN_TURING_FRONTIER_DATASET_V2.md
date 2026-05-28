# v0.9.14 Layerwise Default-Profile Dry-Run + Turing-Frontier Dataset V2 Audit

## Why v0.9.14 Exists

v0.9.13 passed the layerwise shadow promotion probe. The next step is a default-profile dry-run that exercises the default loading path without enabling real promotion or changing the actual default profile. v0.9.14 also starts the Turing-frontier dataset v2 data-grounding work.

## Default-Profile Dry-Run

The layerwise sparse 1B freeze-prune profile is loaded only through a shadow default path. Real promotion remains disabled, `profile_is_default_runtime` remains false, and the production default configuration is not modified. Fallback and rollback paths are checked separately.

## Historical Accuracy Regression Table

The version writes a historical table from v0.9.7 through v0.9.14. Arithmetic compiler-perfect results are not compared as the same scope as bounded-control top1, and diagnostic sweeps are not treated as mainline ability.

## Turing-Frontier Dataset V2

Dataset v2 expands the structured frontier data spectrum while preserving support boundaries. Function, array, recursion, unbounded execution, IO/system-call, trap, review, and natural-language variant cases are included, but current supported and future-domain samples remain strictly separated.

## Non-Claims

This version does not enable real promotion, change the default profile, claim Turing completeness, claim solved program synthesis, claim production readiness, or claim emergence proven.
