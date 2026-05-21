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
