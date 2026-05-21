# High-Load Parallel Runtime & OOD Precision Recheck（高负载并行运行时与分布外精审复查）

## Cache Policy（缓存策略）
- runtime_cache_dir（运行缓存目录）: C:\Users\Air\OneDrive\文档\jianmu-mvp\.jianmu_runtime_cache\run_51368e8b37d3
- project_inside_onedrive（项目位于 OneDrive 内）: True
- user_allows_project_local_cache（用户允许项目内缓存）: True

## Worker Scaling Benchmark（worker 扩展基准）
- worker_counts_tested（测试 worker 数）: [1, 2, 4, 8]
- best_worker_count（最佳 worker 数）: 4
- highload_parallel_speedup_confirmed（高负载并行加速确认）: True

## Serial / Parallel Metric Equivalence（串行/并行指标等价）
- metric_equivalence_passed（指标等价通过）: True

## Buffered Records Integrity（缓冲记录完整性）
- merge_integrity_passed（合并完整性通过）: True
- duplicate_record_count（重复记录数）: 0
- missing_record_count（缺失记录数）: 0

## Runtime Profile（运行时剖析）
- worker_speedup_by_mode（worker 加速）: {'xlarge': {'1': 1.0, '2': 1.267032, '4': 1.605094, '8': 1.589718}}

## OOD Precision Recheck（分布外精审复查）
- ood_precision_distribution（分布外精审分布）: {'true_false_accept': 89, 'near_ood_generalization_candidate': 44, 'hard_ood': 45, 'unknown': 22}

## Canonicalization OOD Recheck（规范化分布外复查）
- canonicalizer_made_supported_count（规范化导致看似支持数）: 0
- reason_not_reproduced（未复现原因）: not_reproduced; likely slice mismatch or detector mismatch against v0.8.1 guard-stress reason

## Updated Mainline Judgment（更新主线判断）
- This version validates high-load runtime instrumentation and OOD recheck records; it does not change the main architecture.

## Non-Claims（非主张）
- This does not prove stable convergence.
- This does not prove general program synthesis.
- This does not prove solved arithmetic, AGI, Transformer replacement, advantage over same-size LLM, or safe real promotion.
