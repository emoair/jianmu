# Bounded Substrate Compiler Permission Failure Taxonomy

v0.9.7.2 exists because the v0.9.7 signal audit passed, but the v0.9.7.1 full-level compiler validation had `PermissionError` failures. Compiler validation is a correctness foundation for the bounded substrate line, so these failures cannot be ignored or hidden behind successful internal evaluation.

This version diagnoses Windows/MSVC temporary-file and process-lifecycle behavior: write source, spawn `cl.exe`, wait for compile/link, run the executable, capture output, write traces, and clean up temporary files. It separates cleanup races, path issues, OneDrive or Windows file locks, process-handle release problems, and true candidate/program compile/runtime errors.

The v0.9.7.1 original metrics are preserved. Patched replay is reported separately and is explicitly only a replay of the failed samples. Independent validation is also reported separately after the temp/process manager fix.

This version does not claim Turing completeness, solved program synthesis, stable convergence, safe real promotion, or production readiness.
