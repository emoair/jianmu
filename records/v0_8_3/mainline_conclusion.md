# Mainline Conclusion Ledger（主线结论账本）

## 本版证明了什么
- worker_count 1/2/4/8 high-load benchmark completed for xlarge.
- metric_equivalence_passed: True

## 本版没有证明什么
- stable convergence; general program synthesis; solved arithmetic; safe real promotion.

## 新瓶颈是什么
- Runtime speedup remains workload-dependent; OOD near-generalization requires review.

## 是否改变主线判断
- False.

## 下一版最小必要动作
- Re-run with full RootForge candidate generation workload and larger OOD slices.

## 哪些结果可以进入 paper draft
- Worker scaling table, cache policy, and OOD precision recheck taxonomy.

## 哪些结果必须复验
- xlarge/full with full candidate generation and more seeds.

## 风险
- pseudo_improvement: false; negative_transfer: false; ood_pollution: true.

## 高负载并行是否真的加速
- True
- best_worker_count: 4

## OneDrive / cache policy 是否仍是风险
- project_inside_onedrive: True; user_allows_project_local_cache: True

## OOD accepted 分类
- true_false_accept: 89
- near_ood_generalization_candidate: 44
- future_domain_candidate: 0
- label_too_strict: 0
- unknown: 22

## canonicalizer_made_it_look_supported 是否复现
- canonicalizer_made_supported_count: 0
- reason_not_reproduced: not_reproduced; likely slice mismatch or detector mismatch against v0.8.1 guard-stress reason
