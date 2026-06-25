# Compiler Invocation Integrity Contract

Compiler correctness must be based on backend subprocess evidence, not frontend event counters. Valid evidence includes `cl.exe`, `link.exe`, and exe run pid, returncode, monotonic timing, artifact paths, and stdout comparison.

