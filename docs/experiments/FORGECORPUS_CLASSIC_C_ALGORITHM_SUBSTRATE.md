# v1.0.3 ForgeCorpus Classic C Algorithm Substrate

## 1. Why Classic C Algorithm Corpus

v1.0.2 showed controlled small-project parsing works, but the corpus was still synthetic-project heavy. v1.0.3 introduces deterministic classic C algorithm families to strengthen function structure, array operations, nested loops, recursion frontier recognition, state updates, algorithmic control flow, and heldout variant generalization.

## 2. Corpus Policy

The primary corpus is deterministic self-generated classic C. Optional manual drop-in corpus is allowed only when the user provides metadata and a permissive license manifest. Unknown, GPL, LGPL, AGPL, proprietary, or missing-license sources are quarantined and do not enter training data.

This version does not automatically fetch GitHub.

## 3. Scope

The scope is controlled single-file classic C algorithms. It is not arbitrary project parsing, multi-file project support, pointer-heavy support, malloc support, file IO support, or system-call support.

## 4. Validation

`cl.exe /Zs` is a syntax frontend filter only. Correctness evidence comes from full compile/link/run/stdout validation or watchdog evaluation.

## 5. Non-Claims

- no arbitrary project parsing completed
- no formal Turing completeness proven
- no solved program synthesis
- no production readiness
- no function/array production support
- no natural language layer completed
- no emergence proven

