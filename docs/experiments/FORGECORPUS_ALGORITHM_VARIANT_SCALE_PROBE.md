# v1.0.3.1 ForgeCorpus Algorithm Variant Scale Probe

## 1. Why Algorithm Variant Scale

v1.0.3 showed that a deterministic classic C algorithm corpus can contribute useful substrate hardening signal. v1.0.3.1 tests a narrower follow-up question: whether the same algorithm semantic skeleton can remain aligned when its surface code changes under controlled requirements.

This probe focuses on variable names, function names, constants, array size, loop direction, boundary values, sorting order, helper-function splitting, recursion base-case variants, matrix dimensions, and stack or queue capacity.

## 2. Requirement-Driven Variants

Each variant is generated from an explicit `AlgorithmRequirementSpec`. The spec records the mutation policies used for the variant and is audited separately from the generated C source.

The generator is deterministic and controlled. It does not use external APIs, LLM APIs, unknown-license code, or automatic GitHub fetching.

## 3. Metric Freshness

The probe emits a fresh run id and version-local records. The metric freshness audit checks that the v1.0.3.1 metrics are not copied from v1.0.2 or v1.0.3 summaries, and that syntax checks are not counted as correctness evidence.

## 4. Scope

This version covers controlled single-file classic C algorithm variants. It is not arbitrary project parsing, multi-file project support, complex pointer support, malloc support, file IO support, or system-call support.

## 5. Validation

`cl.exe /Zs` is used only as a syntax frontend filter. Correctness evidence comes from full compile, link, run, and stdout validation on terminating supported samples.

## 6. Non-Claims

- no arbitrary project parsing completed
- no formal Turing completeness proven
- no solved program synthesis
- no production readiness
- no function/array production support
- no natural language layer completed
- no emergence proven
