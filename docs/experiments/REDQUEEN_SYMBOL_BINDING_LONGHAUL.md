# v1.0.4.1 RedQueen Symbol Binding Longhaul

## 1. Why Symbol Binding

v1.0.4 introduced a controlled C systems frontier substrate for pointer, malloc, file IO, multi-file, and struct patterns. Before JianMu moves toward a wider natural-language layer, it needs a sturdier substrate for identifier recognition and semantic binding: variables, functions, parameters, struct fields, malloc buffers, FILE handles, pointer aliases, and header/source declarations must remain consistently bound through rename and mutation.

## 2. Not Just re.sub

This version permits regex-like surface perturbation only after AST and symbol-table checks. The guard rejects mutation inside string literals, comments, identifier substrings, and macro-like text without a contract. Global string replacement alone is not accepted as semantic rename evidence.

## 3. Longhaul Rule

The full run requires `wall_clock_min_hours >= 6`. If wall clock is below six hours, `longhaul_completed` is false, `recommended_claim_level` cannot be positive, and `blocking_issues` must include `wall_clock_below_minimum`. The runner may continue heldout, replay, extended compile, and equivalence validation work, but it may not use sleep as fake wall-clock evidence.

## 4. Real Compiler Accounting

The version records real `cl.exe`, link, executable-run, and unique compile-unit counts. It also records cached-as-new, duplicate invocation, stubbed validation, and summary-only validation checks. Syntax frontend accounting is kept separate and is not correctness evidence.

## 5. Non-Claims

This version does not claim arbitrary project parsing, memory safety solved, file IO production support, multi-file project production support, formal Turing completeness, solved program synthesis, production readiness, natural-language layer completion, or emergence proven.

