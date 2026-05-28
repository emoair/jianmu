# Bounded Substrate Larger Training Rerun

v0.9.8 exists because v0.9.7 showed a bounded-substrate positive signal, and v0.9.7.1 through v0.9.7.3 audited the signal and restored clean MSVC compiler validation after the PermissionError cleanup issue. This version reruns the bounded substrate probe at larger scale.

The trained state remains within the existing JianMu architecture: bounded substrate routing and scoring state, Root-Colony lifecycle state, nutrient/toxic memory, and bounded program stage statistics. It does not change AtomicSynthesis, canonicalizer, BranchChain semantics, candidate generation semantics, or free inference feature semantics.

Evaluation covers variable declaration, assignment sequence, multi-variable sequence, if/else, bounded for loops, bounded while loops with explicit fuel, nested bounded control, and boundary/future/near-OOD/trap rejection. Real MSVC `cl.exe` validation uses the clean temp/process manager restored in v0.9.7.3 with `compile_worker_count=16`.

Terminal progress bars are observational only. Progress output is not evidence, is not written into metric JSON as a substitute for records, and cannot change training/evaluation/compiler metrics. JSON and JSONL records remain authoritative.

Non-claims: no Turing completeness, no solved arithmetic, no solved program synthesis, no stable convergence, no solved OOD, no safe real promotion, and no production readiness.

