# RedQueen v2 Causal Bandit + Contrastive Forge

## Why v0.9.20 Exists

v0.9.19 found that RedQueen's strongest next step is not more static curriculum volume, but causal scheduling with better contrastive pair coverage. v0.9.20 implements a diagnostic RedQueen v2 bandit scheduler and a Contrastive Forge dataset path.

## Boundary-as-Data-Contract

This version adds the JianMu Architecture Charter. Capability boundaries remain defined by schema, support_status, expected_action, audits, compiler validation, and versioned records. The implementation does not add runtime hardcoded boundary checks in candidate generation, routing, or free inference.

## RedQueen v2 Bandit Scheduler

The scheduler uses v0.9.19 ROI, attribution, risk, and contrastive-pair diagnostics to allocate curriculum arms with an epsilon-greedy policy. Risk penalties come from offline audits and records, not runtime interception.

## Contrastive Forge

Contrastive Forge generates minimal semantic-difference pairs: loop-bound differences, condition-operator differences, update-order differences, output-variable differences, same-semantics different Chinese surfaces, and same-surface different semantics.

## Regression Dashboard, Not Replay Buffer

Regression Dashboard and Capability Balance Report are offline evaluations. They are not replay buffers, anti-forgetting pools, or training-time blockers.

## Experiment Groups

The diagnostic compares v1 static RedQueen, v2 bandit-only, contrastive-only, bandit plus contrastive, and bandit plus contrastive plus HydraBudget.

## Non-Claims

v0.9.20 does not claim Turing completeness, solved program synthesis, production readiness, default-profile change, or production function/array/recursion support.
