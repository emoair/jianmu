# JianMu v0.5 Baseline

## Core Identity

JianMu v0.5 is a Chinese-first deterministic program rewriting runtime with hierarchical semantic neurons, speculative route candidates, compiler-backed execution feedback, RouteMemory, and TraceCache.

## Verified Capabilities

- Chinese-first natural language intent interface
- Technical tokens such as C/int/printf preserved
- Hierarchical semantic neurons
- SemanticFeatures and neuron audit trail
- Multiple RouteCandidates
- CandidateExecutor
- ProgramIR-based C code generation
- gcc/clang/cl sandbox validation
- RouteMemory for route-level experience
- TraceCache for verified result replay
- expected_output_provenance anti-self-certification
- unsupported English NL rejection
- 58 tests passed

## Current Proof Scope

This version only demonstrates a small-domain Chinese-first program rewriting runtime for simple C integer summation/editing tasks.

## Non-Claims

This version does not prove:
- learned router
- general natural language understanding
- general code intelligence
- AGI
- replacement of LLMs
- replacement of compilers
- large-scale software engineering capability
- hardware BPU-level implementation

## Next Research Targets

- Train a tiny learned intent router
- Compare handcrafted neurons vs learned router
- Add benchmark and ablation
- Add more ambiguous Chinese edit tasks
- Add tree-sitter/clang AST
- Add route memory generalization experiments
