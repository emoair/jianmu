# v0.6.8 Scale Smoke Benchmark（规模化冒烟基准） Report

This is a diagnostic Scale Smoke Benchmark（规模化冒烟基准）, not a convergence or performance claim.

## Metrics（指标）

- loaded_sample_count: 6000
- sampled_size: 800
- sampled_split_counts: {'train': 320, 'eval_seen_target_unseen_paraphrase': 160, 'eval_unseen_target': 160, 'eval_ood': 160}
- candidate_generation_success_rate: 1.0
- sample_target_ir_exact_match: 0.4813
- eval_seen_target_targetir_exact_match: 0.0
- eval_unseen_target_targetir_exact_match: 0.575
- eval_ood_rejection_rate: 0.75
- eval_ood_false_accept_rate: 0.25
- paraphrase_group_consistency_sampled: 0.8765
- language_target_unknown_count: 0
- true_missing_layer_rate: 0.0
- early_reject_short_path_rate: 0.35
- runtime_seconds: 1.0742

## Notes（说明）

- BranchChain（分支链）, Confidence-Gated Continuation（置信度守卫式继续）, AtomicSynthesis（原子结构合成）, and TargetIR（目标中间表示） are exercised only in a sampled diagnostic path.
- OOD Evaluation（分布外评测）, Seen-Target Evaluation（已见目标评测）, and Unseen-Target Evaluation（未见目标评测） are reported separately where sampled.

## Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
