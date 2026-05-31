# IronJudge Accounting Reconciliation

## Why v0.9.18.2 Exists

v0.9.18.1 produced 27,800 accounted real-MSVC compiler invocations with clean observed results, but its readiness fields mixed two accounting paths: `main_20k_completed=false` while the recommended claim level described 20K clean evidence. This version exists only to reconcile that accounting conflict.

## Cumulative vs Independent Accounting

v0.9.18.2 explicitly selects cumulative accounting for the v0.9.18.1 records. The recorded levels form a chain: v0.9.18 previous invocations feed `gate_5k`, `gate_5k` feeds `main_20k`, and `main_20k` feeds `extended_50k`.

Under this policy, `main_20k` uses cumulative effective invocations. Since the observed total is 27,800 and the completed invocations are clean, `main_20k` can be reconciled as completed and clean. `extended_50k` remains partial because 27,800 is below 50,000; it is recorded as observed-clean but not completed-clean.

## No New Capability

This version does not add function or array capability, does not open recursion, does not change the default profile, and does not enable real promotion. It only reconciles records and claim semantics.

## Claim Policy

A claim upgrade is allowed only when accounting, readiness, and clean criteria fields agree. v0.9.18.2 reports `ironjudge_20k_clean_frontier_evidence_reconciled` because the reconciled cumulative main_20k path is completed and clean. It does not claim Turing completeness, solved program synthesis, production readiness, or production function/array support.
