# v1.0.6 Dry-run Plan

1. Create `production_shadow_dry_run_v1_0_6` as an explicit opt-in shadow profile.
2. Run the dry-run profile guard before any execution.
3. Route only allowed dry-run policies through the interface adapter.
4. Reuse AtomicSynthesis policy bridge, ExtendedIR, ExtendedEmitterC, and the existing compiler backend.
5. Generate compiler-backed dry-run trace records.
6. Run regression and rollback guards.
7. Emit readiness conservatively.

This plan does not modify the default profile, enable real promotion, or claim production support.
