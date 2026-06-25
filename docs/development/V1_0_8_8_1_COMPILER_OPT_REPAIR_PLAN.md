# v1.0.8.8.1 Compiler / OPT Repair Plan

1. Audit v1.0.8.8 compiler counters for per-invocation backend evidence.
2. Downgrade the v1.0.8.8 compiler claim if only summary counters exist.
3. Separate frontend generated events from backend `cl/link/exe` evidence.
4. Add backend invocation manifest and stdout comparison trace.
5. Restore OPT display and bind it to trace and backend manifest.
6. Detect security interference separately from compiler correctness.
7. Run short real backend validation and replay sampling.

