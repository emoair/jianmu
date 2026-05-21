# v0.8.8 Real Persisted Router-State & External OOD Eval

## 1. Why Persisted State Eval

v0.8.7 is a no-label free-beam probe（无标签自由束探针）, but it may still be questioned as depending on probe scaffolding（探针脚手架）. v0.8.8 saves and reloads router/root/probe state（路由/根/探针状态） so boundary behavior can be checked across runs.

If the current architecture only exposes summary-level state, this version records `persisted_state_support_level = summary_only` rather than claiming full router/root persistence.

## 2. No-Label Reloaded Evaluation

Reloaded inference（重载推理） must not read:

- `boundary_label`
- `expected_action`
- `nutrient_policy` / `toxicity_policy`
- `target_ir` / `expected_output`
- `target_branch_path`

Labels may be used only for evaluation scoring（评估打分）, never for candidate generation or free inference（候选生成或自由推理）.

## 3. External OOD Slice

The external OOD slice（外部分布外切片） is not a direct reuse of the v0.8.5 train/eval split. It contains newly constructed:

- hard unrelated requests（硬无关请求）
- arithmetic-looking traps（算术外观陷阱）
- future-domain candidates（未来能力候选）
- malformed arithmetic-like text（畸形算术样文本）
- near-OOD candidates for quarantine（近邻 OOD 隔离候选）

Near-OOD candidates are not counted as supported success. They remain quarantine / candidate-buffer cases unless the supported boundary spec changes in a later version.

## 4. arXiv Readiness

The run outputs:

- `ready_for_arxiv_technical_report`
- `blocking_issues`
- `recommended_claim_level`
- `non_claims`

If state persistence is only `summary_only`, the report must not claim full persisted router/root proof even when reloaded metrics are strong.

## 5. Non-Claims

This version does not claim:

- stable convergence
- solved arithmetic
- solved OOD
- general program synthesis
- AGI
- Transformer replacement
- same-size LLM advantage
- safe real promotion
