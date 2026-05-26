# Bounded Substrate Signal Audit + Full-Level Rerun

v0.9.7.1 exists because v0.9.7 produced a bounded substrate positive signal, but that signal must be audited before it is treated as mainline evidence. The audit checks per-sample metric provenance, forbidden-field leakage, train/heldout separation, baseline/ablation evidence, compiler validation, and failure examples.

Full-level means using the large v0.9.6 bounded substrate dataset, covering variable declaration, assignment, multi-variable sequence, if/else, bounded for loops, bounded while loops with fuel, nested bounded control, and unsupported/trap/future/near-OOD/hard-OOD boundary categories. Full-level does not mean Turing completeness.

Worker scaling in this version only tests bounded-substrate compiler validation at 8, 16, 32, and 64 MSVC `cl.exe` workers. It does not retest 128/256/512, and it must not trade correctness, boundary safety, or trace integrity for throughput.

This version does not claim Turing completeness, solved program synthesis, stable convergence, safe real promotion, or production readiness.
