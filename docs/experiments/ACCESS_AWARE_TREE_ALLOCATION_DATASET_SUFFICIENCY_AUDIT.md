# v0.9.12.1 Access-Aware Tree Allocation and Dataset Sufficiency Audit

v0.9.12 showed a positive but diminishing 1B lazy-indexed state-budget signal: the active touch ratio was only 0.052 while boundary/future safety and compiler validation remained clean. v0.9.12.1 exists to diagnose whether that cold state is caused by tree allocation imbalance, dataset/curriculum under-activation, intentional future-domain quarantine coldness, or a mix of those factors.

## Tree Allocation Interpretation

The audit interprets JianMu state as trunk, branch, and leaf layers: global routing trunk, major language-family branches, supported bounded-substrate branches, bounded-control branches, candidate leaves, control-template leaves, failure memory, nutrient-toxic memory, routing/scoring slots, and future-domain quarantine branches.

## Dataset Sufficiency Interpretation

Low branch access can mean the dataset does not sufficiently activate a branch. It can also be intentional when future-domain function, array, recursion, unbounded-loop, IO, or system-call paths are correctly quarantined. Supported bounded-control coverage and future-frontier coverage are therefore reported separately.

## Diagnostic Only

Dataset-balanced resampling and access-aware reallocation are diagnostic probes. They do not modify JianMu's core architecture, do not promote a new default profile, and do not claim improved production capability.

## Non-Claims

This version does not claim Turing completeness, solved arithmetic, solved program synthesis, stable convergence, solved OOD, same-size LLM advantage, safe real promotion, production readiness, or emergence proven.
