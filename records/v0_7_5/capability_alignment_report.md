# RootForge Capability Alignment（根铸能力对齐） Report

## Candidate Space Repair（候选空间修复）
- Branch Prior Repair（分支先验修复） covers Literal-Only TargetIR（单字面量目标中间表示）, Literal Value Policy（字面量值策略）, target_builder literal routing（字面量目标构造路由）, and negative-number routing（负数路由）.

## Path-Forcing Smoke Test（强制路径冒烟测试）
- path_forcing_exact_match_rate（强制路径精确匹配率）: 1.0
- path_forcing_literal_only_success_rate（单字面量强制成功率）: 1.0
- path_forcing_precedence_success_rate（优先级强制成功率）: 1.0

## Capability Audit（能力审计）
- synthesizable_by_forced_path_rate（强制路径可合成率）: 1.0
- router_candidate_failure_rate（路由候选失败率）: 0.3333
- synthesis_capability_failure_rate（合成能力失败率）: 0.0
- dataset_capability_mismatch_count（数据能力不匹配数量）: 0

## Beam Result（束搜索结果）
- target_ir_exact_match_top1（Top1 目标中间表示精确匹配）: 0.0
- target_ir_exact_match_beam_oracle（束内上限）: 0.0
- correct_targetir_in_beam_rate（正确目标中间表示在束内率）: 0.0
- candidate_space_failure_rate（候选空间失败率）: 1.0
- ranking_failure_rate（排序失败率）: 0.0

## Root Viability（根系可生性）
- train_low_score_correct_count（训练集低分正确根数量）: 8400
- eval_low_score_correct_count（评测集低分正确根数量）: 0
- low_score_correct_without_action_count（低分正确根无动作数量）: 0

## Regrowth Action（再生动作）
- regrowth_queue_added_count（再生队列加入数量）: 5262
- stable_root_buffer_added_count（稳定根缓冲加入数量）: 7408
- necrosis_queue_added_count（坏死队列加入数量）: 992

## Data Pollution Audit（数据污染审计）
- artifact_suffix_stripped_count（伪影后缀剥离数量）: 203
- artifact_suffix_examples（伪影后缀示例）: [{'raw_text': '28（jm-v070-000029）', 'canonical_text': '28', 'warnings': ['stripped_dataset_artifact_suffix']}, {'raw_text': '二十八（jm-v070-000030）', 'canonical_text': '28', 'warnings': ['stripped_dataset_artifact_suffix']}, {'raw_text': '计算二十八（jm-v070-000031）', 'canonical_text': '28', 'warnings': ['stripped_dataset_artifact_suffix']}]

## Non-Claims（非主张）
- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This is RootForge Capability Alignment（根铸能力对齐）, not a release claim.
