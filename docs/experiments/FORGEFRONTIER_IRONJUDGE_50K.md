# ForgeFrontier + IronJudge 50K

## Why v0.9.18 Exists

v0.9.17 pushed the bounded-control best profile to top1 0.8824, but its compiler validation evidence was still limited to 500 real MSVC invocations. v0.9.18 adds IronJudge to thicken that evidence at 5k, 20k, and optional 50k real compiler-invocation targets, while also opening a strictly experimental function/array frontier probe.

## Compiler Validation Meaning

Compiler validation means generating candidate C, invoking real MSVC `cl.exe`, building an executable, running it, comparing stdout against the post-hoc expected output, and checking that boundary/future paths did not compile incorrectly.

## IronJudge 50K

IronJudge 50K means a target of 50,000 real compiler invocations. It is not cached validation, not an internal evaluator, and not a Python subprocess substitute. If the runtime budget or environment prevents completion, the run is reported as partial with completed invocation counts.

## ForgeFrontier

ForgeFrontier evaluates pure functions without recursion, fixed-size arrays without pointers, function plus bounded control, array plus bounded loop, and limited function-array combinations. Recursion, pointers, IO, system calls, English, and mixed-language boundaries remain isolated.

## Non-Claims

This version does not claim Turing completeness, solved program synthesis, production support, default profile change, or real promotion.
