# RedQueen Controlled Weak Signal Contract

Controlled weak signals are synthetic governance inputs used only to test RedQueen scheduling response.

They may change sample weights, review allocation, replay checks, boundary stress, and difficulty in the opt-in validation plan. They must not change compiler correctness accounting, default runtime profile, production boundary, real promotion flags, or release readiness.

Required invariants:

- `weak_signal_is_synthetic = true`
- `weak_signal_affects_real_correctness = false`
- `weak_signal_affects_scheduling_only = true`
- `production_claim_impact = none`
- production support flags remain false
