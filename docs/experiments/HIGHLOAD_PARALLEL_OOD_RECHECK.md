# High-Load Parallel Runtime & OOD Precision Recheck（高负载并行运行时与分布外精审复查）

## 1. Why High-Load Parallel Benchmark（为什么做高负载并行基准）

v0.8.2 的 quick probe 太轻，serial 只需毫秒级，parallel 调度开销大于计算本身，因此不能作为并行是否有效的结论。

v0.8.3 在 medium / xlarge-light / xlarge 真实工作量下评估 worker_count 1 / 2 / 4 / 8。目标不是改变 JianMu 主架构，而是测量同一评分语义在更高负载下是否具有工程吞吐价值。

## 2. Runtime Cache Policy（运行缓存策略）

- OneDrive 路径不再默认视为禁用条件。
- 用户确认 OneDrive sync disabled。
- runtime_cache_dir 默认可使用项目内 `.jianmu_runtime_cache/`。
- 仍允许用户传入 `D:\jianmu-runtime-cache\` 等外部缓存目录。
- 只避免对正式 records 高频写入。
- 最终 records 仍输出到 `records/v0_8_3/`。

## 3. Buffered Records（缓冲记录）

- worker 写 shard；
- 内存 buffer；
- checkpoint；
- 最终 merge；
- crash 时保留 partial checkpoint。

## 4. OOD Precision Recheck（分布外精审复查）

OOD 不等于全部毒性。必须区分：

- Hard OOD（硬分布外）；
- Near-OOD Generalization Candidate（近邻泛化候选）；
- Future Domain Candidate（未来能力候选）；
- Label Too Strict（标签过严）；
- True False Accept（真正误接收）；
- Unknown（未知）。

## 5. Non-Claims（非主张）

不得声称：

- stable convergence；
- general program synthesis；
- solved arithmetic；
- AGI；
- Transformer replacement；
- advantage over same-size LLM；
- safe real promotion。

