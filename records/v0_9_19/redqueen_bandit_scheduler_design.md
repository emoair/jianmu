# Redqueen Bandit Scheduler Design

Diagnostic only. This is not a capability-improvement claim.

```json
{
  "arm_definition": "data_need_spec or adversarial_pattern",
  "reward_terms": [
    "heldout_gain",
    "candidate_miss_reduction",
    "in_beam_gain"
  ],
  "penalty_terms": [
    "boundary_risk_penalty",
    "regression_penalty",
    "resource_cost_penalty",
    "duplicate_penalty",
    "template_overfit_penalty"
  ],
  "reward_function": "heldout_gain + 0.7*miss_reduction + 0.3*in_beam_gain - boundary_risk_penalty - regression_penalty - resource_cost_penalty - duplicate_penalty - template_overfit_penalty",
  "exploration_policy": "epsilon-greedy with minimum quota per safe arm",
  "exploitation_policy": "ROI-weighted allocation among arms passing Sentinel gates",
  "minimum_exploration_quota": 0.08,
  "safety_circuit_breaker": "pause arm if boundary/future/language false accept increases above zero",
  "cold_start_strategy": "seed arms from v0.9.17 data_need_specs and contrastive-cause templates",
  "low_roi_retirement_policy": "reduce arm by half after two low-ROI windows unless it protects boundary safety",
  "update_interval": "per 10k generated samples or per diagnostic shard",
  "logging_schema": [
    "arm_id",
    "samples",
    "heldout_gain",
    "miss_reduction",
    "in_beam_gain",
    "risk_penalties",
    "reward",
    "action"
  ],
  "readiness_for_implementation": true
}
```
