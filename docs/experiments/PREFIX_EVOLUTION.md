# Prefix-Evolution IR Token Prototype

This is a v0.5.5 development experiment, not a v0.5 release claim.

The goal is to test a minimal form of prefix-level atomic neuron evolution:
stateless prefix neurons compete to emit ProgramIR-oriented tokens under
ground-truth oracle supervision and compiler-backed validation.

This prototype does not train a Transformer, does not train a C character-level
model, and does not claim that a learned router is complete. It also does not
claim AGI, general program generation, or hardware BPU implementation.

Current scope is intentionally tiny:

- Chinese-first prompts for binary integer addition
- ProgramIR token targets such as `INCLUDE_STDIO`, `LITERAL_INT`, `ADD`, and
  `PRINT_EXPR`
- deterministic conversion from token sequence to `ProgramIR` and `CEmitter`
  output
- compiler sandbox execution as the final oracle

The expected output is supplied by `PrefixTrainingTask`; generated stdout is
never used to self-certify correctness.

Future work can explore whether this prefix-level reward mechanism can be
extended into fuller ProgramIR routing chains and later DarwinForge-style
evolution experiments.
