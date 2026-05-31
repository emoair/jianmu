# IronJudge Resumable Scaleup

## Why v0.9.18.1 Exists

v0.9.18 produced positive function/array frontier signals, but IronJudge 5K, 20K, and 50K were all partial. v0.9.18.1 focuses only on strengthening real compiler-validation evidence through resumable continuation.

## Compiler Validation

Compiler validation means using real MSVC `cl.exe`, compiling C, running the produced executable, and comparing stdout with post-hoc expected output. Boundary, future, unsupported, English, mixed-language, recursion, pointer, and IO paths must not enter the supported compiler path.

## Resumable IronJudge

Resumable IronJudge writes checkpoints, shard manifests, completed sample hashes, failure hashes, pending hashes, and per-level accounting. Previous v0.9.18 traces can count only as previous contribution. New validation must be new real compiler invocations, with no cached result counted as new work.

## What This Version Does Not Do

This version does not introduce a new capability boundary, does not open recursion, does not claim production support, and does not enable real promotion.

> Note: We attempted to apply for additional Codex open-source support quota, but the submission flow repeatedly failed. Development continues under quota constraints - unfortunate, but the compiler does not care about our tears.
