# v0.9.17 RedQueen Curriculum + HydraBudget Probe

## Why v0.9.17 exists

v0.9.16 showed that data quality and a stage-balanced Chinese current-supported mix improved the layerwise profile. The next diagnostic step is not to keep adding static data, but to generate new Chinese bounded-control curriculum from observed failure patterns and to test shadow dynamic layerwise budgets.

## RedQueen Curriculum Engine

RedQueen is a compiler-verifier-guided adversarial curriculum loop. It mines weak stages and failure patterns, generates bounded-control program structure from deterministic grammar, renders Chinese input descriptions, derives expected output through evaluator/compiler-compatible IR, and audits the result before use.

## HydraBudget Allocator

HydraBudget is a layerwise sparse budget diagnostic. It considers utilization, touch, candidate-miss contribution, marginal gain, boundary/future risk, cooldown, resource guard, expansion, and rollback. It is shadow-only and does not change the real default profile.

## Safety Principles

Future function, array, and recursion samples do not become current-supported. English and mixed-language samples do not become current-supported. Boundary, trap, and OOD examples must not be accepted as supported. Budget expansion must not amplify bad routes.

## Non-claims

This version does not claim Turing completeness, function/array/recursion support, real promotion, default profile changed, production readiness, solved program synthesis, or emergence proven.
