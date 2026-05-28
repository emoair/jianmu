# v0.9.10 Targeted Candidate-Space Expansion Rerun

## Why v0.9.10 exists

v0.9.8.1 identified candidate miss as the dominant bounded-substrate plateau cause. v0.9.9 then showed, in a diagnostic budget sweep, that a larger candidate-space profile can reduce candidate miss. v0.9.10 turns that best diagnostic profile into a fresh independent rerun.

This version does not continue the sweep. It validates one profile on fresh samples.

## Profile Used

- beam_size = 64
- candidate_budget = 512
- control_template_budget = xlarge
- root_expansion_budget = 8x
- memory_budget = 8x

The profile is a controlled budget configuration, not an architecture change, and is not claimed as JianMu's default architecture.

## Evaluation Surface

The rerun evaluates current bounded-control supported samples and bounded-control hard-supported samples. It also separately evaluates future function, future array, future recursion, unsupported unbounded loop, near-OOD, trap, hard-OOD, and review samples.

Only current supported bounded-substrate and bounded-control hard-supported samples may enter the compiler-supported path. Future-domain and unsupported samples must not be compiled as supported.

## Non-Claims

v0.9.10 does not prove Turing completeness, solved arithmetic, solved program synthesis, production readiness, stable convergence, solved OOD, same-size LLM advantage, safe real promotion, or general program synthesis.
