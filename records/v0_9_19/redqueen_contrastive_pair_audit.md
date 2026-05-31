# Redqueen Contrastive Pair Audit

Diagnostic only. This is not a capability-improvement claim.

```json
{
  "contrast_pair_count": 5,
  "minimal_semantic_difference_pair_count": 5,
  "same_surface_different_semantics_count": 2,
  "same_semantics_different_surface_count": 2,
  "loop_bound_contrast_count": 1,
  "condition_operator_contrast_count": 2,
  "update_order_contrast_count": 1,
  "output_variable_contrast_count": 1,
  "branch_threshold_contrast_count": 2,
  "contrast_pair_compiler_verified_rate": 1.0,
  "contrast_pair_top1_gain_estimate": 0.006,
  "contrast_pair_miss_reduction_estimate": 0.006,
  "contrast_pair_roi_score": 0.82,
  "contrast_pairs_are_underused": true,
  "recommended_contrast_pair_templates": [
    "same surface loop bound, inclusive vs exclusive condition",
    "same variables, sequential update order swapped",
    "same branch threshold, < vs <= operator",
    "same final state, different output variable request"
  ],
  "recommended_next_generation_count": 50000
}
```
