# v0.6.6 Hindsight Branch Re-Ranking（回看式分支重排） Report

This is a Group Beam Selection（组级束搜索） scaffold over top-k BranchPath（分支路径） candidates. It uses TargetIR（目标中间表示） and Paraphrase Group（复述组） feedback after prediction.

## Dataset Summary（数据集摘要）

- dataset size（数据集规模）: 40
- supported group count（支持复述组数量）: 8
- OOD count（分布外数量）: 8
- top_k_candidates（候选保留数量）: 3
- beam_width（束宽）: 5

## Single Winner vs Re-Ranked vs Group Beam（单赢家 / 重排 / 组级束搜索）

- generation 0 single_winner_sample_exact_match（第 0 代单赢家精确匹配）: 0.5
- final single_winner_sample_exact_match（最终单赢家精确匹配）: 0.5
- final reranked_sample_exact_match（最终重排单样本精确匹配）: 0.5
- final group_beam_exact_match（最终组级束搜索精确匹配）: 0.5
- group_beam_consistency（组级束搜索一致性）: 0.875

## Candidate Quadrants（候选四象限）

- candidate_quadrant_counts（候选四象限计数）: {'high_score_correct': 20, 'low_score_correct': 37, 'high_score_wrong': 20, 'low_score_wrong': 29}
- low_score_correct_count（低分正确候选数量）: 37
- high_score_wrong_count（高分错误候选数量）: 20
- rerank_improvement_count（重排改进数量）: 0
- rerank_regression_count（重排退化数量）: 0

## Branch Pruning（分支剪枝）

- wrong_consistent_group_count（一致但错误组数量）: 2
- pruning_candidate_count（剪枝候选数量）: 12
- collapse_penalty_hits（坍缩惩罚触发次数）: 6

## OOD Evaluation（分布外评测）

- ood_rejection_rate（分布外拒绝率）: 1.0
- ood_false_accept_rate（分布外误接收率）: 0.0

## Correct-Low-Score Candidate（低分正确候选） Examples

- aa-toy-001: original_rank=1, rerank_rank=1, pred=add(lit(1),lit(2))
- aa-toy-001: original_rank=2, rerank_rank=2, pred=add(lit(1),lit(2))
- aa-toy-002: original_rank=1, rerank_rank=1, pred=add(lit(1),lit(2))

## Wrong-High-Score Candidate（高分错误候选） Examples

- aa-toy-013: original_score=-1.4333, pred=add(lit(1),lit(2)), true=add(lit(1),mul(lit(2),lit(3)))
- aa-toy-014: original_score=-1.4333, pred=add(lit(1),lit(2)), true=add(lit(1),mul(lit(2),lit(3)))
- aa-toy-015: original_score=-1.4333, pred=add(lit(1),lit(2)), true=add(lit(1),mul(lit(2),lit(3)))

## Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Hindsight Branch Re-Ranking（回看式分支重排） scaffold.
