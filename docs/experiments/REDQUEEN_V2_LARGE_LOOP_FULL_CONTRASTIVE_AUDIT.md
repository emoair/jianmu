# RedQueen v2 Large Loop + Full Contrastive Audit

## Why v0.9.20.1 Exists

v0.9.20 first crossed top1 0.90 for the RedQueen v2 diagnostic path, but its Contrastive Forge audit only materialized a 300-row preview per scale. v0.9.20.1 expands the contrastive dataset into a larger materialized audit, runs a RedQueen v2 large-loop reproducibility probe, and checks whether the v0.9.20 result can be reproduced or strengthened.

## What This Version Does

This version performs larger contrastive materialization, full contrastive pair audit, large-loop training/eval diagnostics, bandit arm stability analysis, real MSVC compiler validation scaleup, Regression Dashboard/Capability Balance offline checks, and v1.0 substrate-freeze readiness assessment.

## What This Version Does Not Do

It does not add a new capability boundary, add recursion support, add production function/array support, change the default profile, or enable real promotion.

## Architecture Charter Compliance

JianMu capability boundaries remain data-contract-defined through dataset schema, support_status, expected_action, audits, compiler validation, and versioned records. This version does not add runtime hardcoded gates in candidate generation, routing, or free inference. Regression Dashboard remains offline evaluation, not a replay buffer or training-time interceptor.

## Non-Claims

This version does not claim Turing completeness, solved program synthesis, production readiness, safe real promotion, default profile change, production function/array support, recursion support, or emergence proven.
