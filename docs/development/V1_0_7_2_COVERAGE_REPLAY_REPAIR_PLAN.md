# v1.0.7.2 Coverage Replay Repair Plan

1. Create a coverage expansion branch from v1.0.7.1.
2. Add shape diversity builders that reuse existing ExtendedIR and ExtendedEmitterC.
3. Add 16-worker replay scheduling with shard indexing and per-sample worker isolation.
4. Run 4-hour coverage and replay validation.
5. Preserve default blocking, malformed opt-in blocking, opt-out rollback, and regression guard evidence.
6. Write trace pack, accounting, coverage review, replay validation, readiness, and mainline conclusion records.
7. Keep production support flags false and do not tag or release.
