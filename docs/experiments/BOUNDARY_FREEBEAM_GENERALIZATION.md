# Boundary Free-Beam Generalization（边界自由束泛化）

## 1. Why Free-Beam Evaluation（为什么做自由束评估）

v0.8.6 的拒绝边界改善是在 Boundary Curriculum Training Probe（边界课程训练探针）中观察到的。v0.8.7 移除标签辅助，只在 Free-Beam Evaluation（自由束评估）/ No-Label Inference（无标签推理）下检查边界是否仍然存在。

## 2. No-Label Inference（无标签推理）

Boundary Label（边界标签）、Expected Action（期望动作）、Nutrient Policy（养分策略）、Toxicity Policy（毒性策略）、TargetIR（目标中间表示）、Expected Output（期望输出）和 Target Branch Path（目标分支路径）不得作为 candidate generation（候选生成）或 free inference（自由推理）特征。标签只用于 evaluation scoring（评估计分）。

## 3. Boundary Generalization（边界泛化）

本版记录 current_supported_retention_rate（当前支持保留率）、hard_ood_rejection_rate（硬分布外拒绝率）、true_false_accept_trap_rejection_rate（真正误接收陷阱拒绝率）、future_domain_isolation_rate（未来能力隔离率）、near_ood_quarantine_rate（近邻分布外隔离率）、overall_ood_false_accept_rate（总体分布外误接收率）、over_rejection_detected（过度拒绝检测）和 freebeam_emergent_rejection_signal（自由束自涌现拒绝信号）。

## 4. Non-Claims（非主张）

- This does not prove stable convergence.
- This does not prove general program synthesis.
- This does not prove solved arithmetic.
- This does not prove OOD solved.
- This does not prove a fully emergent rejection gate.
- This does not prove advantage over same-size LLM.
- This does not prove safe real promotion.
