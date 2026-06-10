# Staged Opt-in Precheck Contract

v1.0.6.1 may create a precheck record for a future staged opt-in candidate, but it must not execute staged opt-in.

Required false fields:

- `staged_opt_in_enabled = false`
- `production_ready = false`
- `production_function_support_completed = false`
- `production_array_support_completed = false`
- `production_recursion_support_completed = false`

The next branch may only be a candidate for review.
