# JianMu v0.5 Release Notes

## Summary

JianMu v0.5 is a Chinese-first deterministic program rewriting runtime for a
small C integer summation and editing domain.

## Highlights

- Chinese-first natural-language interface with C technical tokens preserved
- Hierarchical semantic neuron scaffold with `SemanticFeatures` and audit trail
- Speculative `RouteCandidate` generation with compiler-backed execution feedback
- `RouteMemory` for route-level experience and `TraceCache` for verified replay
- `expected_output_provenance` anti-self-certification guard
- Unsupported English natural-language rejection
- Unsupported non-addition expression rejection for `1-2`, `1*2`, and `1/2`

## Verified Baseline

- Full test command: `python -m pytest tests/ -v`
- Expected release result after this patch: all tests pass, no skipped tests
- Supported sandbox compilers: `gcc`, `clang`, or MSVC `cl.exe`

## Non-Claims

JianMu v0.5 does not claim learned routing, general natural-language
understanding, general code intelligence, AGI, replacement of LLMs, replacement
of compilers, large-scale software engineering capability, or hardware
BPU-level implementation.

## Scope Notes

Negative literals are supported only in limited v0.5 scenarios such as appending
`-2`. Systematic arithmetic parsing, subtraction, multiplication, division, and
AST-level expression rewriting remain out of scope.
