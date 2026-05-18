# JianMu MVP v0.3 Baseline

## Status

This is the clean baseline snapshot before v0.5 development.

## Core Capabilities

- Deterministic IntentRouter
- ProgramIR-based structural generation
- Atomic expert composition
- CEmitter
- GCC/Clang sandbox validation
- Runtime execution validation
- TraceCache
- Scoring
- Limited Chinese/English intent normalization
- Numeric generalization such as 1+2+3 -> 6
- Cache correctness: only fully correct paths are cached

## Current Proof Scope

This version only demonstrates a minimal compiler-validated structural rewriting runtime in a tiny C integer summation domain.

It does not prove:
- general code intelligence
- AGI
- replacement of LLMs
- replacement of compilers
- scalability to real software projects
- true AST-level rewrite
- general natural language understanding

## Next Version Target

v0.5 should extend this baseline toward:
- addition
- subtraction
- multiplication
- division
- zero
- negative numbers
- multi-digit numbers
- parentheses
- expression tree ProgramIR
- stronger red-team tests
