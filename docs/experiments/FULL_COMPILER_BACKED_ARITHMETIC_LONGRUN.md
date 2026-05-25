# v0.9.5 Full Compiler-Backed Arithmetic Longrun

v0.9.5 scales the v0.9.4.3 fresh compiler-backed arithmetic spot signal into a larger compiler-backed longrun probe.

The v0.9.4.3 result showed that fresh arithmetic samples can be compiled by MSVC `cl.exe`, executed as generated binaries, and verified against held-out expected outputs while preserving boundary guards. A spot audit is still bounded: it is smaller, has less runtime exposure, and does not stress checkpointing or sustained trace capture.

This version counts as compiler-backed longrun evidence only when supported samples are compiled with a real C compiler, run as executables, traced per sample, checked against expected output only after candidate generation, and paired with boundary samples that are not routed into the supported compiler path. It also tracks overlap with v0.9.4.1 and v0.9.4.3 samples, token-spacing patch use, latency, failures, and partial/checkpoint status.

The following do not count as compiler-backed longrun evidence:

- internal evaluator execution
- Python subprocess execution
- cached result replay
- summary-only metrics
- partial modes marked as completed

This version does not claim solved arithmetic, full program synthesis, stable convergence, solved OOD, same-size LLM advantage, safe real promotion, production readiness, or Turing completeness.
