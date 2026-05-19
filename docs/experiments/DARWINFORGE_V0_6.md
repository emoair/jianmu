# v0.6 DarwinForge Scaffold

This document defines the minimal v0.6 DarwinForge scaffold. It is a
development experiment, not a JianMu v0.5 release claim and not a completed
DarwinForge system.

## 1. Why v0.6 Exists

v0.5.7 showed that Chinese intent contains learnable signals for route/task
classification, but it was a flat classifier.

v0.5.8 showed that the TargetIR regeneration chain can run, but it used
oracle-assisted inference and flat structure-label classification. It remains a
calibration experiment, not the intended learned router.

v0.5.9 corrected the direction toward a BranchChain scaffold, but its toy
evolution can degenerate because it lacks layer-wise population preservation,
strong BranchPath-to-TargetIR binding, hard-case replay, and candidate-level
fitness.

v0.6 connects BranchChain, AtomicSynthesis, Compiler Sandbox validation, and
fitness evolution into the first minimal DarwinForge loop.

## 2. Three-Layer Model

1. BranchChain

   ```text
   input_text -> layered BranchPath
   ```

2. AtomicSynthesis

   ```text
   BranchPath + surface slots -> TargetIR atoms
   ```

3. DarwinForge

   ```text
   candidates -> fitness -> selection -> mutation -> replay
   ```

The model does not patch old source code and does not train C source text.

## 3. Genotype vs Phenotype

`BranchPath + AtomicExpert parameters` is the genotype.

`TargetIR + generated C program` is the phenotype.

Compiler behavior, runtime output, expected output, unsupported correctness, and
TargetIR structural similarity act as natural selection.

## 4. Fitness Hierarchy

Correctness priority:

1. unsupported correctness
2. TargetIR structural similarity
3. expected_output_match
4. compile_success
5. run_success
6. path length / execution efficiency
7. cacheability / determinism

Execution efficiency must not outrank correctness.

## 5. Oracle Boundary

Forbidden during candidate generation:

- `expression_oracle`
- `parse_controlled_expression`
- `target_ir` label
- `expected_output` label
- generated output as self-certification

Allowed:

- dataset ground truth generation
- evaluation
- fitness scoring after prediction
- oracle upper bound baseline

Candidate generation may use only the latest input, optional previous TargetIR,
surface features, BranchChain decisions, AtomicExpert plans, and learned or
mutated candidate parameters.

## 6. Evolution Policy

DarwinForge v0.6 must avoid global population collapse:

- layer-wise population preservation
- option coverage preservation
- elite preservation per layer
- random immigrants per layer
- mutation around high-scoring paths
- hard-case replay
- no global population collapse

Every generation must keep all active layers represented. Every enabled option
must keep at least minimal coverage, or record a disabled reason.

## 7. Non-Claims

- This does not prove AGI.
- This does not prove Transformer replacement.
- This does not prove hardware BPU implementation.
- This does not prove general program synthesis.
- This does not train C source text.
- This is a minimal DarwinForge scaffold.

