# v0.9.11 Hundred-Million State Budget Probe

## Why v0.9.11 exists

v0.9.8.1 identified candidate miss as the bounded-substrate plateau cause. v0.9.9 showed that diagnostic candidate-space budget expansion reduces candidate miss. v0.9.10 reproduced the targeted profile on fresh samples. v0.9.11 probes whether larger audited state budgets keep reducing candidate miss while preserving boundary/future safety and compiler validation.

## State Budget Definition

State budget means JianMu internal auditable state capacity, not neural network parameters. The units cover candidate fragment bank entries, control-flow template bank entries, stage-specific generation profiles, root/sub-root expansion entries, failure-pattern memory slots, nutrient-toxic memory slots, routing/scoring profile slots, and bounded-control specialized candidate pools.

## Materialization Level

Every profile reports one of: fully_materialized, lazy_indexed, compressed_indexed, logical_budget_only, or simulated_budget. A lazy or logical budget must not be described as a fully materialized in-memory parameter set.

## What Is Not Allowed

This probe must not turn a diagnostic budget into a new architecture, must not bypass memory guard, must not use cached compiler results as validation, and must not claim Turing completeness.

## Non-Claims

v0.9.11 does not prove Turing completeness, solved arithmetic, solved program synthesis, production readiness, stable convergence, solved OOD, same-size LLM advantage, safe real promotion, general program synthesis, or emergence proven.

