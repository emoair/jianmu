# Compiler Failure Taxonomy

- Original compiler invocations: 600
- Original success/failure: 555/45
- Classified failures: 45
- Dominant category: compile_syntax_error
- Engineering issue dominant: True
- Candidate error dominant: False
- Patched rerun executed: True
- Patched correct rate: 1.0
- Original result preserved: True

## Failure Category Distribution

- compile_syntax_error: 45

Dominant observed pattern: failed expressions contained adjacent sign tokens such as `--`. MSVC tokenizes these as decrement operators before parsing unary signs. The patched rerun only spaces adjacent sign tokens in generated C source; it does not change candidate generation or scoring.

## Claim Scope

This audit classifies the v0.9.4.1 compiler spot failures. It does not claim solved arithmetic, stable convergence, solved OOD, same-size LLM advantage, safe real promotion, production readiness, or a full compiler-backed longrun.
