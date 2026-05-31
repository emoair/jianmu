# Mainline Conclusion

Diagnostic only. This is not a capability-improvement claim.

```json
{
  "proved": [
    "RedQueen v0.9.17 gains can be attributed by diagnostic spec and pattern ROI",
    "Regression Sentinel found no bounded-control or boundary safety drift",
    "A RedQueen v2 causal scheduler design is ready for implementation"
  ],
  "not_proven": [
    "Turing completeness",
    "solved program synthesis",
    "production readiness",
    "safe real promotion",
    "stable convergence",
    "solved OOD",
    "general program synthesis",
    "default profile changed",
    "function/array production support",
    "recursion support",
    "emergence proven"
  ],
  "why_autopsy": "identify RedQueen bottlenecks before scaling data further",
  "most_effective_patterns": [
    "bounded_for_loop",
    "if_else_nested",
    "if_else_basic",
    "bounded_while_with_fuel"
  ],
  "low_roi_patterns": [],
  "template_overfit_risk": 0.00061,
  "pseudo_diversity_score": 0.99512,
  "contrast_pairs_underused": true,
  "causal_curriculum_plan": {
    "plan_name": "redqueen_v2_causal_curriculum",
    "target_top1": 0.9,
    "target_candidate_miss": 0.045,
    "top_patterns_to_increase": [
      "bounded_for_loop",
      "if_else_nested",
      "if_else_basic",
      "wrong_top1_contrast_pairs"
    ],
    "patterns_to_keep": [
      "boundary_preservation_negatives",
      "condition_boundary"
    ],
    "patterns_to_reduce": [],
    "patterns_to_redesign": [],
    "patterns_to_quarantine": [],
    "recommended_data_mix": {
      "causal_patterns": 0.5,
      "contrastive_pairs": 0.25,
      "boundary_negatives": 0.1,
      "regression_sentinel": 0.15
    },
    "recommended_contrast_pair_ratio": 0.25,
    "recommended_boundary_negative_ratio": 0.1,
    "recommended_stage_weights": {
      "bounded_for_loop": 0.00015712,
      "if_else_nested": 0.00015712,
      "if_else_basic": 0.00015712,
      "bounded_while_with_fuel": 0.00015712,
      "nested_bounded_control": 0.00015712,
      "multi_variable_update": 0.00015712,
      "condition_boundary": 0.00015712,
      "loop_bound_off_by_one": 0.00015712
    },
    "expected_gain_target": 0.015,
    "expected_candidate_miss_target": 0.045,
    "safety_constraints": [
      "no future function/array/recursion in current_supported train",
      "Regression Sentinel must pass",
      "boundary false accept must remain zero"
    ],
    "diagnostic_source": "v0.9.19 autopsy only",
    "contrast_pair_templates": [
      "same surface loop bound, inclusive vs exclusive condition",
      "same variables, sequential update order swapped",
      "same branch threshold, < vs <= operator",
      "same final state, different output variable request"
    ],
    "sentinel_eval_ratio": 0.15,
    "sentinel_passed": true
  },
  "bandit_scheduler_design": {
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
  },
  "readiness": {
    "redqueen_autopsy_completed": true,
    "spec_attribution_completed": true,
    "pattern_roi_completed": true,
    "template_overfit_audit_completed": true,
    "contrastive_pair_audit_completed": true,
    "regression_sentinel_completed": true,
    "causal_curriculum_plan_completed": true,
    "bandit_scheduler_design_completed": true,
    "bandit_diagnostic_simulation_completed": true,
    "top_positive_patterns": [
      "bounded_for_loop",
      "if_else_nested",
      "if_else_basic",
      "bounded_while_with_fuel"
    ],
    "low_roi_patterns": [],
    "high_risk_patterns": [
      "boundary_preservation_negatives"
    ],
    "template_overfit_risk_score": 0.00061,
    "pseudo_diversity_score": 0.99512,
    "severe_template_collapse_detected": false,
    "contrast_pairs_are_underused": true,
    "regression_sentinel_passed": true,
    "capability_balance_score": 0.94,
    "recommended_scheduler": "epsilon_greedy_scheduler",
    "ready_for_redqueen_v2_bandit_scheduler": true,
    "ready_for_causal_curriculum_generation": true,
    "recommended_claim_level": "redqueen_autopsy_complete_ready_for_v2_bandit",
    "blocking_issues": [],
    "required_next_run": "implement RedQueen v2 causal curriculum with bandit scheduler in diagnostic mode"
  },
  "paper_v2_technical_report_candidates": [
    "spec-level diagnostic attribution",
    "pattern ROI table",
    "Regression Sentinel framing",
    "bandit scheduler design"
  ],
  "still_not_proven": [
    "Turing completeness",
    "solved program synthesis",
    "production readiness",
    "safe real promotion",
    "stable convergence",
    "solved OOD",
    "general program synthesis",
    "default profile changed",
    "function/array production support",
    "recursion support",
    "emergence proven"
  ]
}
```
