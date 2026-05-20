# RootForge Capability Alignment（根铸能力对齐）

## 1. Why Capability Alignment（为什么需要能力对齐）

v0.7.4 RootForge Growth Dynamics（根铸生长动力学） connected RootForge（根铸） concepts, but the core result still showed Candidate Space Failure（候选空间失败）: correct TargetIR（目标中间表示） did not enter the beam.

Before adding more growth dynamics, v0.7.5 checks whether supported samples are theoretically synthesizable under the current BranchChain（分支链） and AtomicSynthesis（原子结构合成） capability range.

## 2. Branch Prior Repair（分支先验修复）

This version repairs BranchNeuron（分支神经元） priors for:

- Literal-Only TargetIR（单字面量目标中间表示）
- Literal Value Policy（字面量值策略）
- negative-number routing（负数路由）
- target_builder literal routing（字面量目标构造路由）

Examples such as `49`, `-6`, and `输出五` should have a chance to route through `literal_only → literal_value → canonical_arithmetic_targetir`.

## 3. Path-Forcing Smoke Test（强制路径冒烟测试）

Path-Forcing Smoke Test（强制路径冒烟测试） is an offline Capability Audit（能力审计） tool.

Allowed:

- use `target_branch_path` to force a BranchPath（分支路径）
- canonicalize raw_text（原始文本） into canonical_text（规范文本）
- call AtomicSynthesis（原子结构合成）
- compare predicted TargetIR（目标中间表示） with target labels

Forbidden:

- use forced paths in candidate generation（候选生成）
- use target labels as inference features（推理特征）
- let Canonical Symbol Layer（规范符号层） generate TargetIR（目标中间表示） or C source

If path forcing fails, the issue is AtomicSynthesis（原子结构合成）, features, or canonicalization. If path forcing succeeds but beam search fails, the issue is BranchChain（分支链） candidate generation or scoring.

## 4. Capability Audit（能力审计）

Capability Audit（能力审计） separates:

1. synthesizable_by_forced_path（强制路径可合成）
2. router_candidate_failure（路由候选失败）
3. synthesis_capability_failure（合成能力失败）
4. dataset_capability_mismatch（数据能力不匹配）

This prevents a single candidate_space_failure（候选空间失败） metric from hiding where the failure actually occurs.

## 5. Metric Scope Repair（指标口径修复）

v0.7.4 mixed train-time root viability（根系可生性） with eval-time beam oracle（束内上限） metrics. v0.7.5 splits these into:

- train_low_score_correct_count（训练集低分正确根数量）
- eval_low_score_correct_count（评测集低分正确根数量）
- low_score_correct_without_action_count（低分正确根无动作数量）

Every low-score correct root must enter at least one action path: stable buffer（稳定缓冲）, regrowth queue（再生队列）, or necrosis queue（坏死队列）.

## 6. Data Pollution Audit（数据污染审计）

Canonical Symbol Layer（规范符号层） strips dataset artifact suffixes（数据集伪影后缀） such as:

- `（jm-v070-xxxxxx）`
- `(jm-v070-xxxxxx)`
- `（sample-xxx）`
- `(sample-xxx)`

raw_text（原始文本） is preserved. canonical_text（规范文本） is cleaned. Source Map（源映射） warnings include `stripped_dataset_artifact_suffix`.

## 7. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is RootForge Capability Alignment（根铸能力对齐）, not a release claim.
