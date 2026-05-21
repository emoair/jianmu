# Persisted Router External OOD Eval（持久化路由与外部 OOD 评估）

## Persisted State Support Level（持久化状态支持等级）
- persisted_state_support_level: summary_only
- This run records available probe summaries honestly; it does not claim full BranchChain/root persistence.

## State Save / Load（状态保存与加载）
- state_saved: True
- state_loaded: True
- state_manifest_path: records\v0_8_8\state\state_manifest.json
- forbidden_field_in_state_count: 0

## No-Label Reloaded Evaluation（无标签重载评估）
- no_label_inference_passed: True
- forbidden_field_access_count: 0
- current_supported_retention_rate: 1.0
- overall_ood_false_accept_rate: 0.0

## External OOD Slice（外部分布外切片）
- external_ood_total_count: 3000
- category_distribution: {'external_hard_ood': 750, 'external_arithmetic_traps': 750, 'external_future_domain': 750, 'external_near_ood': 750}

## External OOD Metrics（外部分布外指标）
- external_ood_false_accept_rate: 0.0
- hard_ood_rejection_rate: 1.0
- trap_rejection_rate: 1.0
- future_domain_isolation_rate: 1.0
- near_ood_quarantine_rate: 1.0

## Multi-Seed Stability（多 seed 稳定性）
- stable_across_seeds: True
- seed_metrics: [{'seed': 42, 'current_supported_retention_rate': 1.0, 'overall_ood_false_accept_rate': 0.0, 'hard_ood_rejection_rate': 1.0, 'trap_rejection_rate': 1.0, 'future_domain_isolation_rate': 1.0, 'near_ood_quarantine_rate': 1.0, 'no_label_inference_passed': True, 'over_rejection_detected': False}, {'seed': 43, 'current_supported_retention_rate': 1.0, 'overall_ood_false_accept_rate': 0.0, 'hard_ood_rejection_rate': 1.0, 'trap_rejection_rate': 1.0, 'future_domain_isolation_rate': 1.0, 'near_ood_quarantine_rate': 1.0, 'no_label_inference_passed': True, 'over_rejection_detected': False}, {'seed': 44, 'current_supported_retention_rate': 1.0, 'overall_ood_false_accept_rate': 0.0, 'hard_ood_rejection_rate': 1.0, 'trap_rejection_rate': 1.0, 'future_domain_isolation_rate': 1.0, 'near_ood_quarantine_rate': 1.0, 'no_label_inference_passed': True, 'over_rejection_detected': False}]

## Persisted State Consistency（持久化状态一致性）
- persisted_state_consistency_passed: True
- max_abs_metric_delta: 0.0

## arXiv Readiness Assessment（arXiv 准备度评估）
- ready_for_arxiv_technical_report: False
- recommended_claim_level: needs_more_validation
- blocking_issues: ['persisted state support is summary_only, not full router/root state']

## Failure Analysis（失败分析）
- Summary-only state remains a blocker for full persisted router/root proof.

## Updated Mainline Judgment（更新主线判断）
- Reloaded summary-state behavior can be audited, but full persisted router/root state remains future work.

## Non-Claims（非主张）
- This does not prove stable convergence.
- This does not prove solved arithmetic.
- This does not prove solved OOD.
- This does not prove general program synthesis.
- This does not prove same-size LLM advantage.
- This does not prove safe real promotion.
