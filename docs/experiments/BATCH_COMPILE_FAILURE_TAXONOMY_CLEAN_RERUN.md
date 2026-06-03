# Batch Compile Failure Taxonomy Clean Rerun

v0.9.27.1 exists because v0.9.27 showed positive function/array and Turing-frontier scaleup signals, but batch full-compile validation was not clean. Readiness was therefore downgraded and this version isolates the failure modes before any review or freeze candidate can be considered.

The MSVC frontend filter uses `cl.exe /Zs` as a syntax-only efficiency filter. Syntax pass is not correctness evidence; semantic behavior, stdout, halting, and watchdog classification still require full compile/run/stdout or watchdog validation.

The taxonomy separates wrong stdout, timeout, semantic, watchdog, toolchain, infrastructure, and data-contract failures. Replay is reported honestly: v0.9.27 traces include sample hashes and compiler outcomes, not replayable source text.

Repair is diagnostic and curriculum-oriented: RedQueen assignments and repair datasets target failure families without sample-id blacklists, keyword hard rejection, runtime gates, routing hardcodes, candidate generation hardcodes, or hidden failed categories.

Non-claims: no production support, no formal Turing completeness proof, no v1.0 release, no function/array production readiness.
