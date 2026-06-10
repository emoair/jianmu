# Shadow Profile Boundary Contract

The shadow profile must remain explicit opt-in:

- `default_profile = false`
- `real_promotion_enabled = false`
- `user_facing_enabled = false`
- `release_enabled = false`
- `production_support_claim_enabled = false`
- `rollback_required = true`
- `audit_trace_required = true`
- `compiler_validation_required = true`

Enabled bridge policies are experimental only:

- `canonical_function_targetir`
- `canonical_array_targetir`
- `canonical_function_array_targetir`
- `canonical_structured_recursion_targetir`

Each remains marked as `production_supported = false`, `dry_run_enabled = true`, and `experimental_active_bridge = true`.
