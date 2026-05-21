# JianMu v0.8 Technical Report TODO（技术报告待办）

## Verification（核验）

- Verify all record paths cited in `docs/papers/JIANMU_V0_8_TECHNICAL_REPORT.md`.
- Re-check v0.7.0-v0.7.2 exact record paths and fill N/A only where records are truly absent or non-comparable.
- Verify the v0.6.9 OOD metric wording because before/after sections and diagnostic summaries use slightly different scopes.
- Confirm whether a local `JIANMU_SET_THEORETIC_ROUTING.md` exists in another branch before formalizing the theory section.
- Verify v0.8.1.1 record paths after merging the records branch:
  - `records/v0_8_1_1/mainline_conclusion.md`
  - `records/v0_8_1_1/metric_reconciliation_report.md`
  - `records/v0_8_1_1/xlarge_reproduction_summary.json`

## Figures（图表）

- Add system overview diagram.
- Add version timeline diagram.
- Add global beam trend chart for v0.8.0-v0.8.1.1.
- Add OOD false accept taxonomy chart for v0.8.1.
- Add root lifecycle state chart for v0.7.9, v0.8.0, and v0.8.1.1.

## Before Public Preprint（公开预印本前）

- Run v0.8.2 Runtime Parallelism & Buffered Records（运行时并行与缓冲记录）.
- Re-run xlarge/full after runtime parallelism.
- Complete or partially complete full/longrun with checkpoint records.
- Add same-size LLM / Transformer baseline.
- Add heuristic / flat classifier baseline table.
- Add compiler/run success table.
- Add OOD guard stability on larger OOD slices.
- Add diagrams:
  - BranchChain（分支链）.
  - RootFork Sub-Beam（根叉子束）.
  - Root Colony Lifecycle（根群生命周期）.
  - Toxic Nutrient / OOD Guard（毒性养分 / 分布外守卫）.
  - Shadow Promotion（影子晋升）.
- Export PDF.
- Decide GitHub / Zenodo / arXiv timing.

## Before First arXiv Submission Candidate（第一版 arXiv 候选前）

- Complete v0.8.8 Real Persisted Router-State & External OOD Eval（真实持久化路由状态与外部分布外评估）.
- Add external held-out OOD slice（外部保留分布外切片）.
- Add more seed runs.
- Add same-size LLM / Transformer baseline plan（同体量 LLM / Transformer 基线计划）.
- Add table separating:
  - training probe（训练探针）.
  - no-label free-beam probe（无标签自由束探针）.
  - persisted-state eval（持久化状态评估）.
  - external OOD eval（外部分布外评估）.
- Add diagrams:
  - BranchChain（分支链）.
  - RootFork / Root Colony（根叉 / 根群）.
  - Boundary-Aware Curriculum（边界感知数据课程）.
  - No-Label Free-Beam Evaluation（无标签自由束评估）.
- Export PDF.
- Decide whether to submit as technical report or wait for v0.9 baseline.

## Export（导出）

- Export report to PDF after metrics are re-verified.
- Add generated figures under `docs/papers/assets/`.
- Preserve Markdown as the source of truth before any PDF export.

## Publication（发布）

- Decide later whether to publish to GitHub Release / Zenodo.
- Do not submit arXiv yet.
- Wait for v0.8.2 or v0.9 before formal preprint.
- Keep all claims bounded to recorded evidence.

## Do Not Claim Yet（暂不主张）

- AGI.
- Transformer replacement.
- General program synthesis.
- Solved arithmetic.
- Optimal code generation.
- Superiority over same-size LLM.
- Safe real promotion.
- Stable convergence.
- OOD solved.
- Fully emergent rejection gate as final proof.

## v0.8.7 Path Verification TODO（路径核验）

- Verify after merging records branch: records/v0_8_7/mainline_conclusion.md, records/v0_8_7/freebeam_boundary_report.md, records/v0_8_7/no_label_inference_guard.json, records/v0_8_7/boundary_generalization_metrics.json.
