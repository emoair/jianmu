# RedQueen Iteration Loop Contract

The iteration loop is a governance loop, not a production capability boundary.

The allowed loop is:

1. Load the previous RedQueen plan.
2. Create a read-only pre-iteration metrics snapshot.
3. Execute the validation schedule through the existing staged opt-in validation path.
4. Create a post-iteration metrics snapshot.
5. Compare metric deltas.
6. Audit governance drift, overreaction, and underreaction.
7. Generate the next validation plan.

The loop must keep model training, weight updates, default profile modification, real promotion, user-facing enablement, and official release disabled.
