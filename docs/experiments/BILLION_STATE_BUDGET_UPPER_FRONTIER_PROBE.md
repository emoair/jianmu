# v0.9.12 Billion-State Budget Upper Frontier Probe

## Why v0.9.12 exists

v0.9.11 showed smooth positive scaling up to a 100M lazy-indexed state budget. v0.9.12 continues the upper-frontier probe to 300M, 600M, and 1B to evaluate benefit, cost, active access, and safety.

## What 1B State Budget Means

The 1B budget is JianMu internal state budget, not neural-network parameter count. It is not assumed to be fully materialized. It covers candidate fragments, control templates, root/sub-root expansion entries, failure memory, nutrient-toxic memory, routing/scoring slots, and bounded-control specializations.

## Materialization Honesty

Every profile records whether it is fully_materialized, compressed_indexed, lazy_indexed, logical_budget_only, or simulated_budget. A lazy/logical budget must not be described as fully materialized.

## Access Audit

The probe records target_state_units, actual_state_units_allocated, unique_state_units_touched, total_lookup_count, hot/cold ratios, touch_ratio, and lazy realized/unrealized units. If the 1B touch_ratio is low, the result must say the target budget completed but active usage was low.

## Non-Claims

v0.9.12 does not prove Turing completeness, solved arithmetic, solved program synthesis, production readiness, stable convergence, solved OOD, same-size LLM advantage, safe real promotion, general program synthesis, or emergence proven.

