# v0.9.2 Arithmetic Curriculum Dataset

## 1. Purpose

v0.9.2 builds a dataset foundation for future arithmetic curriculum probes. It does not train JianMu, does not alter Root-Colony Routing or BranchChain architecture, and does not claim solved arithmetic.

## 2. Supported Arithmetic

The current supported class contains integer literals, unary minus, binary `+`, `-`, `*`, exact integer `/`, parentheses, standard precedence, and left associativity. Division is supported only when the denominator is nonzero and the division is exact. Supported samples may contain JSON AST `target_ir` and integer `expected_output` for supervised scoring and audit.

## 3. Boundary Classes

The dataset separates current-supported arithmetic from unsupported arithmetic boundaries, true-false-accept traps, future-domain candidates, near-OOD arithmetic, hard OOD, and label review candidates. Non-supported classes must not contain `target_ir` or `expected_output`.

## 4. Leakage Controls

Free inference forbidden fields are recorded in each sample's leakage guard: `target_ir`, `expected_output`, `target_branch_path`, `boundary_label`, `expected_action`, `nutrient_policy`, and `toxicity_policy`. These fields are labels or audit data, not inference features.

## 5. Non-Claims

This dataset-only version does not claim solved arithmetic, stable convergence, solved OOD, general program synthesis, same-size LLM advantage, safe real promotion, or production readiness.
