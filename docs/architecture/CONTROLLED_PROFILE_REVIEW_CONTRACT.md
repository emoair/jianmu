# Controlled Profile Review Contract

Controlled profile review is a review gate after dry-run and before staged opt-in. It reads v1.0.6 records and performs targeted replay, coverage review, rollback stress, and default contamination checks.

It cannot change the default profile. It cannot enable staged opt-in. It cannot mark production support complete.

Allowed positive result: `ready_for_staged_opt_in_candidate = true`.
