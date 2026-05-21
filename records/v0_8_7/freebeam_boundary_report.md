# Boundary Free-Beam Generalization Probe（边界自由束泛化探针）

## Source Training State（源训练状态）
- source_training_available: True

## Held-Out Boundary Slices（保留边界切片）
- heldout_slice_counts: {'heldout_current_supported': 600, 'heldout_hard_ood': 600, 'heldout_true_false_accept_trap': 600, 'heldout_future_domain_candidate': 600, 'heldout_near_ood_generalization_candidate': 409, 'heldout_mixed_boundary': 2809}
- leakage_check_passed: True

## No-Label Inference Guard（无标签推理防泄漏）
- no_label_inference_passed: True
- forbidden_field_access_count: 0

## Free-Beam Boundary Metrics（自由束边界指标）
- current_supported_retention_rate: 1.0
- hard_ood_rejection_rate: 1.0
- true_false_accept_trap_rejection_rate: 1.0
- future_domain_isolation_rate: 1.0
- near_ood_quarantine_rate: 1.0
- overall_ood_false_accept_rate: 0.0

## Comparison With v0.8.6 Probe（与 v0.8.6 探针对比）
- delta_ood_false_accept: 0.0
- delta_current_supported_retention: 0.0

## Failure Examples（失败样例）
- false_accept_examples: 0
- false_reject_supported_examples: 0

## Rejection Diagnostics（拒绝诊断）
- freebeam_emergent_rejection_signal_confirmed: True
- partial_boundary_generalization: False
- boundary_probe_did_not_generalize: False
- over_rejection_detected: False

## Updated Mainline Judgment（更新主线判断）
This is a no-label free-beam probe, not a full-scale convergence claim.

## Non-Claims（非主张）
- This does not prove stable convergence.
- This does not prove general program synthesis.
- This does not prove solved arithmetic.
- This does not prove OOD solved.
- This does not prove a fully emergent rejection gate.
- This does not prove advantage over same-size LLM.
- This does not prove safe real promotion.
