# Turing Proof Function Array Frontend Scaleup

v0.9.27 follows the true 12 hour frontier endurance result from v0.9.26.1. It adds an MSVC frontend syntax filter for training-time screening, then performs separate batch full-compile validation after training.

The frontend filter uses `cl.exe /nologo /TC /WX /Zs`: syntax only, no object file, no executable, and no program run. Syntax pass is not correctness evidence.

The version scales experimental function definition/call, local scope, parameter passing, fixed-size arrays, array read/write/loops, and function-array interop. Function and array samples remain experimental frontier data and are not production support.

It also writes a constructive Turing expressivity proof artifact with counter-machine mapping notes, WHILE-language mapping notes, finite witness traces, and limitations. Finite validation is not a formal proof of Turing completeness.

The longhaul rule is wall_clock_min_hours = 6. If the run is below 6 hours, readiness must be partial.
