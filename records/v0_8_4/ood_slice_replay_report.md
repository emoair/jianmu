# OOD Slice Replay & Generalization Boundary（分布外切片回放与泛化边界）

## Source Slice Loading（源切片加载）
- source_branch（源分支）: v0.8.1-ood-toxicity-longrun-scale
- source_record_paths（源记录路径）: ['records/v0_8_1/ood_guard_stress.jsonl', 'records/v0_8_1/ood_toxicity_by_class.json', 'records/v0_8_1/ood_toxicity_longrun_metrics.json']
- replay_sample_count（回放样本数）: 200
- partial_replay（部分回放）: False
- missing_field_counts（缺失字段计数）: {'sample_id': 0, 'raw_text': 0, 'canonical_text': 0, 'ood_class': 0, 'accepted_as_supported': 0, 'false_accept_reason': 0}

## Supported Boundary Spec（支持边界规格）
- Current supported boundary remains bounded arithmetic / TargetIR routing. English arithmetic stays future-domain by default.

## Canonicalizer Reason Replay（规范化原因回放）
- old_canonicalizer_reason_count（旧规范化原因计数）: 67
- new_canonicalizer_reason_count（新规范化原因计数）: 0
- canonicalizer_reason_confirmed（规范化原因确认）: False
- reason_not_reproduced（未复现原因）: not_reproduced; old v0.8.1 guard-stress reason was present but current detector did not reproduce it

## OOD Boundary Classification（分布外边界分类）
- ood_boundary_distribution（分布外边界分布）: {'future_domain_candidate': 193, 'true_false_accept': 32, 'hard_ood': 55}

## Candidate Datasets（候选数据集）
- supported_expansion_candidates（支持域扩展候选）: 0
- future_domain_candidates（未来能力候选）: 193
- true_false_accept_cases（真正误接收案例）: 32
- label_review_cases（标签复审案例）: 0

## Paper Relevance（论文相关性）
- This records the boundary audit needed before treating near-OOD samples as supported expansion candidates.

## Updated Mainline Judgment（更新主线判断）
- OOD accepted samples remain mixed. Candidate datasets are audit outputs only, not training-label changes.

## Non-Claims（非主张）
- This does not prove stable convergence.
- This does not prove general program synthesis.
- This does not prove solved arithmetic, AGI, Transformer replacement, advantage over same-size LLM, safe real promotion, or automatic near-OOD success.
