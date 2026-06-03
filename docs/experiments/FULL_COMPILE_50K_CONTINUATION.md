# v0.9.28.1 Full Compile 50K Continuation

## Why v0.9.28.1 Exists

v0.9.28 reached `ready_for_v1_0_rc1_branch` under conservative wording, but its 50K full-compile continuation was not completed. v0.9.28.1 only adds evidence thickness by accounting for the prior clean 20K from v0.9.27.1 and attempting 30K new full compile/link/run/stdout validations.

## Accounting Rule

The previous clean 20K comes from v0.9.27.1. New continuation invocations must be real new validations. Cached or duplicate results cannot be counted as new evidence.

`total_accounted_invocations = previous_clean_invocations + new_continuation_invocations`.

## Cleanliness Rule

Correctness requires full compile/link/run/stdout validation or watchdog classification. Syntax checks are not correctness evidence. Wrong stdout, timeout, permission, cleanup, boundary/future misroute, and recursion/pointer/IO production compile counts must remain zero for a clean 50K claim.

## Non-Claims

- No new capability.
- No production support.
- No default profile change.
- No formal Turing completeness proof.
- No v1.0 release.
