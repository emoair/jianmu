# Boundary Curriculum Training Probe（边界课程训练探针）

## 1. Why Boundary Curriculum Training（为什么做边界课程训练）

v0.8.5 built the Boundary-Aware Dataset（边界感知数据集）, but it did not prove that rejection boundaries can emerge naturally. v0.8.6 uses that dataset in a training probe（训练探针） to test whether Hard OOD（硬分布外） and True False Accept Trap（真正误接收陷阱） toxic pressure can reduce false accepts.

## 2. No Hard-Coded Rejection Gate（不手写拒绝门）

- boundary labels（边界标签） are used only for reward / evaluation.
- boundary labels are not used as inference features.
- no keyword if/else rejection gate is added.
- rejection behavior must be represented through path-score style probe metrics, not source-code rules.

## 3. Dataset Artifact Policy（数据工件策略）

- Files larger than 50MB should not be newly committed as naked JSONL in future dataset versions.
- Large future datasets should use shard + manifest（分片 + 清单）.
- Git should prefer generator, manifest, audit, and small samples for 10M / 30M / 100M scale work.
- v0.8.5 existing medium / large files are treated as historical artifacts and reported, not retroactively deleted here.

## 4. Boundary Metrics（边界指标）

- current_supported_retention_rate（当前支持保留率）
- hard_ood_rejection_rate（硬分布外拒绝率）
- true_false_accept_trap_rejection_rate（真正误接收陷阱拒绝率）
- future_domain_isolation_rate（未来能力隔离率）
- near_ood_quarantine_rate（近邻分布外隔离率）
- false_accept_toxicity_rate（误接收毒性率）
- false_reject_supported_rate（支持样本误拒率）
- emergent_rejection_signal（自涌现拒绝信号）

## 5. Non-Claims（非主张）

This does not claim stable convergence, general program synthesis, solved arithmetic, solved OOD, a fully emergent rejection gate, advantage over same-size LLM, or safe real promotion.
