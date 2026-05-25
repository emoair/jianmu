# v0.9.4 Real Compiler Arithmetic Spot Audit

v0.9.4 exists because v0.9.3.2 verified a non-periodic arithmetic signal with
per-sample candidate traces, but the backend was still an internal evaluator.
This version asks whether a bounded sample of that signal survives a real local
C compiler and executable run path.

## Backend Boundaries

`internal_evaluator` means the project evaluates arithmetic internally. It is
useful for auditing candidate traces, but it is not compiler-backed evidence.

`python_subprocess_executor` means an isolated Python subprocess executed a safe
arithmetic check. It is external execution evidence, but it is not a C compiler.

`real_c_compiler` requires detecting gcc, clang, or cl, generating a minimal C
program, invoking the compiler through subprocess, running the produced
executable, and comparing stdout to the expected output only after candidate
generation.

`unavailable` means no safe external execution backend could be used.

## Real Compiler-Backed Verification

For supported integer arithmetic samples, v0.9.4 generates a restricted C
program containing only integer arithmetic over digits, spaces, parentheses, and
the operators `+`, `-`, `*`, and `/`. The program has no user input, file I/O,
network access, dynamic allocation, or system calls. Boundary samples are not
sent to the supported compiler path; doing so is recorded as a boundary compiler
misroute.

## Honest Downgrade

If no local C compiler is available, the run must report
`python_subprocess_executor`, `internal_evaluator`, or `unavailable` rather than
claiming compiler-backed verification.

## Non-Claims

This version does not prove solved arithmetic, stable convergence, solved OOD,
general program synthesis, same-size LLM advantage, safe real promotion,
production readiness, or a full compiler-backed longrun.
