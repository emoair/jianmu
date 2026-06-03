# Batch Compile Cleanliness Rule

Batch full-compile validation is clean only when full compile/run/stdout or watchdog validation is clean for the required sample count.

Required conditions: compiler correctness rate is `1.0`, wrong stdout is `0`, terminating-known timeout is `0`, permission and cleanup errors are `0`, boundary/future misroutes are `0`, and recursion/pointer/IO are not compiled as production-supported paths.

Timeout samples may be clean only when they are correctly classified as timeout-unknown or nonterminating by the watchdog contract. Terminating-known timeout remains a validation failure.
