# Boundary Curriculum Training Probe（边界课程训练探针）

## Dataset Loading（数据集加载）
- dataset_scale_used（数据规模）: large
- train/eval（训练/评测）: 12000 / 3000

## Artifact Policy（数据工件策略）
- artifact_policy_passed（工件策略通过）: True
- oversized_file_count（超大文件数）: 2

## Curriculum Stage Results（课程阶段结果）
- curriculum_stages_completed（完成课程阶段）: 6

## Boundary Metrics Before / After（边界指标前后）
- current_supported_retention_rate（当前支持保留率）: 1.0 -> 1.0
- hard_ood_rejection_rate（硬分布外拒绝率）: 0.0 -> 1.0
- true_false_accept_trap_rejection_rate（真正误接收陷阱拒绝率）: 0.0 -> 1.0
- overall_ood_false_accept_rate（总体分布外误接收率）: 1.0 -> 0.0

## Emergent Rejection Diagnostics（自涌现拒绝诊断）
- emergent_rejection_signal_confirmed（自涌现拒绝信号确认）: True
- over_rejection_detected（过度拒绝检测）: False

## Supported Retention Safety（支持域保留安全）
- supported_retention_preserved（支持域保留安全）: True

## OOD Toxicity Reduction（分布外毒性下降）
- toxic_false_accept_reduction（毒性误接收下降）: 1.0

## Failure Analysis（失败分析）
- This is a probe, not a full proof of natural rejection. If metrics do not generalize, downstream training remains required.

## Updated Mainline Judgment（更新主线判断）
- Boundary pressure can be measured without hard-coded rejection gates; downstream free evaluation is still required.

## Non-Claims（非主张）
- This does not prove stable convergence, solved arithmetic, OOD solved, fully emergent rejection, same-size LLM advantage, or safe real promotion.
