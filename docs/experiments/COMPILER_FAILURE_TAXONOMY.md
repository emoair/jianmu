# v0.9.4.2 Compiler Failure Taxonomy

v0.9.4.2 investigates the 45 failed samples from the v0.9.4.1 MSVC-backed arithmetic spot audit.

v0.9.4.1 showed that 555 of 600 supported arithmetic samples compiled with `cl.exe`, ran as subprocess executables, and matched the expected output. That result is useful compiler-backed evidence, but the remaining 45 failures cannot be ignored or automatically treated as model errors. They may come from C source generation, MSVC command-line handling, temporary path behavior, runtime failures, wrong candidate expressions, arithmetic semantic mismatch, unsafe-expression blocking, or trace/recording gaps.

This version classifies every original failure into a fixed taxonomy:

- `compile_syntax_error`
- `compile_toolchain_error`
- `compile_type_error`
- `runtime_error`
- `runtime_timeout`
- `wrong_output`
- `unsafe_expression_blocked`
- `overflow_or_semantic_risk`
- `trace_or_recording_error`
- `unknown`

The original v0.9.4.1 metrics are preserved. If an engineering rerun is performed, patched metrics are reported separately and are not written over the original 555/600 result.

This version does not claim solved arithmetic, stable convergence, solved OOD, general program synthesis, same-size LLM advantage, safe real promotion, production readiness, or a full compiler-backed longrun.
