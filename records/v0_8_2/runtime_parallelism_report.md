# Runtime Parallelism & OOD Precision Audit（运行时并行与分布外精确审计）

## Runtime Cache（运行时缓存）
- runtime_cache_dir（运行时缓存目录）: D:\jianmu-runtime-cache\run_7ac55808904b
- project_inside_onedrive（项目位于 OneDrive 内）: True

## Buffered Records（缓冲记录）
- buffered_record_count（缓冲记录数）: 800
- checkpoint_count（检查点数）: 1

## Serial vs Parallel Equivalence（串行/并行等价）
- metric_equivalence_passed（指标等价通过）: True
- speedup_ratio（加速比）: 0.259648

## Worker Scaling（worker 扩展）
- worker_count（worker 数）: 8
- compile_worker_count（编译 worker 数）: 4

## Runtime Profile（运行时剖析）
- samples_per_second（每秒样本数）: 3357.632376

## OOD Precision Audit（分布外精确审计）
- ood_precision_distribution（分布外精确分布）: {'true_false_accept': 89, 'near_ood_generalization_candidate': 44, 'hard_ood': 45, 'unknown': 22}

## Canonicalization OOD Audit（规范化分布外审计）
- canonicalizer_made_supported_count（规范化导致看似支持数）: 0

## Updated Mainline Judgment（更新主线判断）
- global_correct_targetir_in_beam_rate parallel（并行全局束正确率）: 0.75
- ood_false_accept_rate parallel（并行分布外误接收率）: 0.665

## Non-Claims（非主张）
- This does not prove stable convergence.
- This does not prove general program synthesis.
- This does not prove solved arithmetic, AGI, Transformer replacement, advantage over same-size LLM, or safe real promotion.
