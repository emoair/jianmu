# v0.6.9 Large Dataset Full Training Probe

This document defines the v0.6.9 Large Dataset Full Training Probe（大数据集全量训练探针） over the v0.6.8 Large Architecture-Aligned Dataset（大规模架构对齐数据集）.

## 1. Why full training probe（为什么做全量训练探针）

v0.6.8 generated 6000 deterministic local samples and ran a Scale Smoke Benchmark（规模化冒烟基准）. The next question is whether the current BranchChain（分支链） and DarwinForge（达尔文进化炉） dynamics improve when given more training samples and a larger candidate population.

This probe is meant to answer whether the issue is merely training volume or whether the current structure, surface features, rejection layers, and fitness shaping still need architectural work. It is not a performance release.

## 2. Parameter scaling（参数规模提升）

This probe scales:

- population_per_layer（每层种群数量）;
- top_k_candidates（候选保留数量）;
- generations（训练代数）;
- checkpoint（检查点） summaries;
- training curve（训练曲线） records.

Modes:

- quick: population_per_layer = 16, generations = 5, top_k = 3, train_sample_limit = 800
- medium: population_per_layer = 32, generations = 20, top_k = 5, train_sample_limit = 2400
- full: population_per_layer = 64, generations = 40, top_k = 5, train_sample_limit = all train split

If full mode is too slow, the report must say so rather than inventing results.

## 3. Stratified evaluation（分层评测）

The probe reports Full-Split Evaluation（全切分评测） and Stratified Evaluation（分层评测） by:

- split;
- input_mode through Input-Mode Metrics（输入模式指标）;
- expression_family through Expression-Family Metrics（表达式族指标）;
- structure_policy;
- unsupported_reason;
- rejected_by_layer;
- reject_type.

## 4. Known diagnostic targets（已知诊断目标）

The report highlights:

- zh_number_expression false reject（中文数字表达误拒）;
- unsupported_arithmetic false accept（不支持算术误接收）;
- task_scope rejection distribution（任务范围层拒绝分布）;
- arithmetic_family unsupported rejection（算术族不支持拒绝）;
- structure_policy unsupported rejection（结构策略不支持拒绝）.

These are diagnostics, not hardcoded fixes.

## 5. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Large Dataset Full Training Probe（大数据集全量训练探针）, not a release claim.

