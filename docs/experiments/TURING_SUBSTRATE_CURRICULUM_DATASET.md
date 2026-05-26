# v0.9.6 Turing Substrate Curriculum Dataset

## Why v0.9.6 exists

The arithmetic line has reached bounded compiler-backed validation, including
the v0.9.5 arithmetic longrun and the v0.9.5.1 compiler-concurrency scaling
probe. The next step is not to claim Turing completeness. The next step is to
prepare auditable curriculum data for the program-language structures that are
needed before any such claim could even be evaluated.

## What "Turing substrate" means

Turing substrate means a prerequisite data foundation for Turing-completeness
related structures: variables, state updates, sequencing, conditionals, and
bounded control flow. It does not mean JianMu is Turing complete.

## Supported current subset

The current supported subset is `bounded_integer_c_subset`:

- integer variables;
- `long long` declarations;
- assignment;
- statement sequences;
- `if` / `else`;
- bounded `for` loops with small constant bounds;
- bounded `while` loops with explicit fuel;
- deterministic integer stdout via `printf("%lld\n", result)`.

## Not supported yet

The current dataset explicitly does not support unbounded loops, recursion,
pointers, arrays, dynamic memory, file IO, user input, function calls beyond
`main`, undefined behavior, system calls, floating point, random/time behavior,
concurrency, macros, or preprocessor logic.

## Compiler validation

v0.9.6 uses real MSVC `cl.exe` through the `vcvars64.bat` environment when
available. The compiler validation probe uses `compile_worker_count = 16`
because v0.9.5.1 identified it as the best local throughput point. This is a
validation spot, not a full compiler-backed longrun.

## Non-claims

This version does not claim Turing completeness, solved program synthesis,
solved arithmetic, stable convergence, solved OOD, same-size LLM advantage,
safe real promotion, or production readiness.
