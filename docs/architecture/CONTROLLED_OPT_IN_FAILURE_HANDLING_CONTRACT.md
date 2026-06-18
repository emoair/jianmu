# Controlled Opt-in Failure Handling Contract

Blocking failures include compiler failure, stdout mismatch, timeout, rollback failure, trace write failure, replay drift, default profile contamination, template bypass, marker IR direct compile, and summary-only validation.

Blocking failures downgrade readiness. They never allow production claims.
