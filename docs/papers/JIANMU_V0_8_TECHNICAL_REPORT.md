# JianMu: Nutrient-Guided Root-Colony Routing for Compiler-Verified Program Synthesis

Chinese subtitle: JianMu: a nutrient-guided root-colony routing system for compiler-verified program synthesis.

Report status: Technical Report Draft（技术报告草稿）, Not a formal paper yet（尚非正式论文）.

Record scope: This draft summarizes local repository evidence from v0.5.7 to v0.8.7. It cites repository documents and records only, and does not modify or reinterpret original experimental data.

This report does not claim stable convergence, general program synthesis, AGI, Transformer replacement, solved arithmetic, optimal code generation, production readiness, safe real promotion, or advantage over same-size LLM baselines.

## Abstract

v0.8.7 update: In v0.8.7, JianMu extended the v0.8.6 boundary-curriculum probe into a no-label free-beam generalization probe. On held-out boundary slices, the no-label inference guard passed with zero forbidden field access. Current-supported retention remained 1.0, while hard-OOD rejection, true-false-accept-trap rejection, future-domain isolation, and near-OOD quarantine each reached 1.0 under the bounded probe criteria. Overall OOD false accept was 0.0, with no false accept or false reject examples recorded. These results strengthen the evidence for boundary-aware rejection behavior, but they do not prove stable convergence, solved OOD, safe real promotion, or advantage over same-size LLMs. 中文说明：v0.8.7 将 v0.8.6 的训练探针正信号推进到 No-Label Free-Beam（无标签自由束） held-out 正信号，但仍不是完整收敛证明，也不是同体量 LLM 对比结论。

JianMu is a compiler-verified routing and synthesis prototype. It routes raw Chinese/math input through Canonical Symbol Layer（规范符号层）, BranchChain（分支链）, RootFork Sub-Beam Regrowth（根叉子束再生）, Nutrient-Zone Root Colony（养分区根群）, Toxic Nutrient（毒性养分） accounting, Shadow Promotion（影子晋升）, AtomicSynthesis（原子结构合成）, and Compiler Sandbox（编译器沙箱） validation.

The strongest v0.8 evidence is diagnostic rather than final: Path-Forcing Smoke Test（强制路径冒烟测试） separated AtomicSynthesis（原子结构合成） capability from routing failure; RootFork Sub-Beam Regrowth（根叉子束再生） rescued paths missed by global beam; Colony Nutrient Activation（根群养分激活） made local root lifecycle states observable; and Colony Scale Stress Probe（根群规模压力探针） showed scale-sensitive improvement in global beam.

After metric reconciliation and xlarge reproduction in v0.8.1.1, JianMu confirmed a strong scale-induced routing signal under the bounded experimental setup: the xlarge same-seed run reached 0.8167 global correct TargetIR-in-beam rate, while an alternate-seed/light reproduction reached 1.0. Candidate-space failure decreased to 0.1833 and 0.0 respectively. These results do not prove stable convergence or general program synthesis, but they strengthen the evidence that Root-Colony scale affects routing coverage. v0.8.1.1 将 xlarge 强规模信号从未验证推进为已确认，但仍不构成通用程序合成、稳定收敛、同体量 LLM 优势、或安全真实晋升证明.

## 1. Introduction

Direct natural-language-to-code generation is difficult to inspect, difficult to reject safely, and difficult to roll back when a model follows the wrong semantic path. JianMu explores a different prototype direction: route input into TargetIR（目标中间表示）, synthesize from a structured path, and verify generated behavior with compiler/run feedback.

The goal is not to produce visually impressive or optimal code. JianMu currently optimizes route-to-verification: whether a verifiable path exists, whether the routing system can find it without reading answer labels during free evaluation, and whether failures can be localized to candidate generation, ranking, synthesis, OOD guard, or lifecycle resource limits.

## 2. System Overview

The current JianMu v0.8 line uses these components:

- Canonical Symbol Layer（规范符号层） normalizes raw Chinese/math text into canonical_text（规范文本） and Source Map（源映射）. It does not emit TargetIR（目标中间表示） or C source.
- BranchChain（分支链） proposes layered routing decisions.
- RootFork Sub-Beam Regrowth（根叉子束再生） starts Prefix-Conditioned Sub-Beam（前缀条件子束） search near weak fork points.
- Nutrient-Zone Root Colony（养分区根群） groups rescued paths into local Nutrient Zones（养分区） and local Root Colonies（根群） instead of broadcasting them globally.
- Toxic Nutrient（毒性养分） treats OOD false accept（分布外误接收） and unsupported false accept as negative lifecycle feedback.
- Shadow Promotion（影子晋升） evaluates proposed colony influence on a shadow copy before any real promotion. Real promotion remains disabled in the v0.8.7 evidence summarized here.
- AtomicSynthesis（原子结构合成） and Compiler Sandbox（编译器沙箱） generate TargetIR（目标中间表示） from BranchPath（分支路径） and validate generated programs through compile/run checks.

Free-Beam Evaluation（自由束评测） does not read target_branch_path, target_ir, or expected_output. Teacher-Guided Diagnostic（教师引导诊断） may use those labels only after generation for diagnosis, reward construction, and offline path-forcing audits. Compiler/run feedback is treated as hard verification for generated test programs, not as proof of optimal code generation.

## 3. Training and Evolution Timeline

### v0.5 Baselines

Goal: establish learned routing and arithmetic TargetIR（目标中间表示） baselines.

Result: v0.5.7 produced an early learned route/task/supported classifier baseline with route_id_accuracy 0.805 and supported_accuracy 0.965. v0.5.8 produced a narrow 1M-parameter arithmetic TargetIR probe with target_ir_exact_match 0.805 and compile_success_rate 1.0.

Failure discovered: these baselines were narrow and did not contain later RootForge（根铸） dynamics, root lifecycle, OOD toxicity accounting, or safe promotion mechanisms.

Next response: v0.6 introduced BranchChain（分支链） and DarwinForge（达尔文进化炉） scaffolds.

### v0.6 BranchChain / DarwinForge Scaffold

Goal: build architecture-aligned dataset consumption, confidence gates, paraphrase checks, hindsight reranking, and large dataset probes.

Result: v0.6.8 consumed 6000 samples and produced candidate_generation_success_rate 1.0 on an 800-sample smoke benchmark, but eval_seen_target_targetir_exact_match was 0.0. v0.6.9 medium training kept before and after target_ir_exact_match at 0.5481 and train target_ir_exact_match at 0.6325, with zh_number_expression_false_reject_rate 1.0.

Failure discovered: more training population, top_k, or generations did not solve symbol grounding or unsupported arithmetic false accept.

Next response: v0.7 moved toward Symbol Grounding（符号接地）, Canonical Symbol Layer（规范符号层）, and path-level diagnostics.

### v0.7 RootFork and Root Colony

Goal: determine whether Chinese symbol grounding, path forcing, wide beam search, sub-beam regrowth, root lifecycle, and local colonies could clarify where routing failed.

Result: v0.7.0 showed raw symbol grounding failed; v0.7.1 showed canonicalization reduced Chinese-number false reject; v0.7.5 proved forced paths were 100% synthesizable; v0.7.6 showed sub-beam rescue could recover paths missed by global beam; v0.7.7 showed direct global assimilation caused negative transfer; v0.7.8 made local colonies safer but inactive; v0.7.9 activated local root lifecycle.

Failure discovered: global beam remained weak, OOD false accept remained high, and crude global weight updates harmed routing.

Next response: v0.8 used scale stress and OOD toxicity pressure tests without enabling real promotion.

### v0.8 Scale Stress and OOD Toxicity

Goal: test whether larger train/eval/OOD slices, larger beam, more cycles, and larger root budgets improve global beam and local stability while keeping OOD toxicity visible.

Result: v0.8.0 completed small/medium/large scale stress runs. Large global_correct_targetir_in_beam_rate reached 0.5017, candidate_space_failure_rate fell to 0.4983, and stable roots increased with scale. However OOD toxicity stayed near 0.67. v0.8.1 completed the large OOD toxicity long-run probe. Its most common false accept reason was canonicalizer_made_it_look_supported, and a guard candidate reduced OOD false accept from 0.335 to 0.235 while arithmetic retention stayed 1.0.

Failure discovered: scale helped supported routing more than OOD rejection. OOD guard ambiguity became a primary bottleneck.

Next response: v0.8.1.1 reconciled metric definitions and reproduced the xlarge signal before treating it as paper-relevant evidence.

### v0.8.1.1 Overnight Metric Reconciliation and XLarge Reproduction

Why it was needed: the v0.8.1 overnight branch produced a strong xlarge signal, but it also had a pytest failure, sample-count mismatch, guard baseline ambiguity, before/after metric conflicts, and root lifecycle final-state ambiguity.

What it did:

- repaired the failing pytest case;
- added Metric Reconciliation v2（指标口径校验 v2）;
- added Split Diagnostics（切分诊断）;
- reran xlarge with the same seed;
- reran xlarge-light with an alternate seed;
- fixed guard baseline accounting so xlarge guard metrics use the current xlarge baseline;
- clarified cumulative_nourished_event_count（累计有养分事件数） versus final_nourished_root_count（最终有养分根数）;
- wrote a Mainline Conclusion Ledger（主线结论账本）.

Result: pytest was green with 480 passed and 28 skipped; metric_consistency_passed was true; inconsistency_count was 0; split mismatch was explained as dataset_capacity; xlarge same-seed global beam was 0.8167 with candidate failure 0.1833; alternate-seed/light global beam was 1.0 with candidate failure 0.0; reproduced_strong_signal was true.

Limitations: full and longrun modes were not completed; real promotion remained disabled; no same-size LLM or Transformer baseline was added; the result remains bounded to the controlled TargetIR setting.

### v0.8.7 Boundary Free-Beam Generalization Probe

Why it was needed: v0.8.6 was a Boundary Curriculum Training Probe（边界课程训练探针）. It needed a follow-up that removed labels from inference, evaluated Free-Beam Evaluation（自由束评估） / No-Label Inference（无标签推理）, and used held-out boundary slices.

What it did:

- added No-Label Inference Guard（无标签推理防泄漏）;
- built held-out boundary slices（保留边界切片）;
- ran Free-Beam Boundary Eval（自由束边界评估）;
- computed Boundary Generalization Metrics（边界泛化指标）;
- wrote Free-Beam Rejection Diagnostics（自由束拒绝诊断）.

Result: no_label_inference_passed was true; forbidden_field_access_count was 0; heldout leakage check passed; current_supported_retention_rate was 1.0; overall_ood_false_accept_rate was 0.0; false_accept_examples and false_reject_supported_examples were both 0; freebeam_emergent_rejection_signal_confirmed was true under v0.8.7 probe criteria.

Limitations: this is not real persisted router-state evaluation yet, not an external OOD benchmark, not full/longrun, not a same-size LLM comparison, and not evidence for safe real promotion.

## 4. Experiments

### Table 1: Early Baselines（早期基线）

| Version | Experiment | Dataset / Sample Count | Key Metrics | Conclusion | Non-Claim |
|---|---:|---:|---|---|---|
| v0.5.7 | Learned Route Classifier Baseline（学习路由分类基线） | train 800 / eval 200 | route_id_accuracy 0.805; task_family_accuracy 0.735; supported_accuracy 0.965 | Useful early learned route/task/supported baseline | Not RootForge（根铸） and not general synthesis |
| v0.5.8 | 1M Arithmetic TargetIR Probe（百万参数算术目标中间表示探针） | train 5000 / eval 1000 | target_ir_exact_match 0.805; compile_success_rate 1.0 | Narrow arithmetic route can score high | Does not prove Root Colony（根群） dynamics or broad arithmetic |

### Table 2: Candidate Space Diagnosis（候选空间诊断）

| Version | Experiment | Dataset / Sample Count | Key Metrics | Conclusion | Non-Claim |
|---|---:|---:|---|---|---|
| v0.7.3 | Wide-Beam Backtracking Search（宽束回溯搜索） | train 200 / eval 100 / ood 100 | correct_targetir_in_beam_rate 0.0; candidate_space_failure_rate 1.0 | Wide beam alone did not put correct TargetIR in beam | Does not prove synthesis impossible |
| v0.7.4 | RootForge Growth Dynamics（根铸生长动力学） | quick probe | candidate_space_failure_rate 1.0; low_score_correct_count 88 | Exposed candidate-space and metric consistency gaps | Does not prove RootForge convergence |
| v0.7.5 | RootForge Capability Alignment（根铸能力对齐） | quick probe | path_forcing_exact_match_rate 1.0; synthesis_capability_failure_rate 0.0; correct_targetir_in_beam_rate 0.0 | Forced path separated synthesis capability from routing failure | Does not prove free routing success |

### Table 3: RootFork and Colony Results（根叉与根群结果）

| Version | Experiment | Dataset / Sample Count | Key Metrics | Conclusion | Non-Claim |
|---|---:|---:|---|---|---|
| v0.7.6 | RootFork Sub-Beam Regrowth（根叉子束再生） | medium | global_correct_targetir_in_beam_rate 0.1; teacher_subbeam_correct_targetir_rate 1.0; subbeam_rescue_rate 0.375 | Local sub-beam rescue was effective | Teacher sub-beam is diagnostic, not free evaluation |
| v0.7.7 | RootFork Global Assimilation（根叉全局吸收） | train 800 / eval 300 / ood 150 | global beam before 0.2733, after 0.1; branch_neuron_updated_count 19281 | Crude global assimilation caused negative transfer | No evidence for safe global promotion |
| v0.7.8 | Nutrient-Zone Root Colony（养分区根群） | train 800 / eval 300 / ood 150 | nutrient_zone_count 19; colony_count 19; ood false accept after promotion 0.3333 | Local colony framing was safer than global assimilation | Lifecycle was not yet activated |
| v0.7.9 | Colony Nutrient Activation（根群养分激活） | train 800 / eval 300 / ood 150 | keep_local_colony_count 17; nourished_root_count 136; stable_root_count 700; real_promoted_colony_count 0 | Local lifecycle activated under shadow promotion | Global beam did not improve |

### Table 4: Scale and OOD（规模与分布外）

| Version | Experiment | Dataset / Sample Count | Key Metrics | OOD Metric | Conclusion | Non-Claim |
|---|---:|---:|---|---|---|---|
| v0.8.0 | Colony Scale Stress Probe（根群规模压力探针） | small/medium/large completed | global beam: small 0.2933, medium 0.2733, large 0.5017; OOD toxicity near 0.67 | OOD toxicity remained high | Scale improved global beam and stable roots | Scale did not solve OOD toxicity |
| v0.8.1 | OOD Toxicity Stress & Long-Run Scale Probe（分布外毒性压力与长时规模探针） | large completed; xlarge/full not verified in report branch | global beam 0.5017; stable_root_count 1239 | OOD false accept 0.335 to 0.235 after guard; arithmetic retention 1.0 | OOD guard candidate improved rejection without hurting retention | Does not prove stable OOD handling |
| v0.8.1.1 | Overnight Metric Reconciliation & XLarge Reproduction（过夜指标口径校验与 xlarge 复验） | requested xlarge 3000/1000/500; actual 2200/600/200 due to dataset_capacity | xlarge same-seed global beam 0.8167; alt-seed/light global beam 1.0; candidate failure 0.1833 / 0.0 | OOD false accept 0.335 to 0.235 after guard; arithmetic retention 1.0 | confirmed strong xlarge scale signal; metric consistency passed; pytest green | full/longrun not completed; no real promotion; no LLM baseline |

| v0.8.7 | Boundary Free-Beam Generalization Probe（边界自由束泛化探针） | large dataset; heldout current 600 / hard OOD 600 / trap 600 / future 600 / near-OOD 409 / mixed 2809 | no_label_inference_passed true; forbidden_field_access_count 0; current_supported_retention_rate 1.0; overall_ood_false_accept_rate 0.0 | hard OOD rejection 1.0; trap rejection 1.0; future isolation 1.0; near-OOD quarantine 1.0 | v0.8.6 boundary signal survived no-label free-beam held-out evaluation; no false accept / false reject examples | not persisted router-state eval; not external OOD; no same-size LLM baseline; not full-scale convergence |

Interpretation of v0.8.1.1: scale-induced routing phase-transition candidate strengthened, but the evidence remains bounded-domain and is not a general synthesis proof.

Interpretation of v0.8.7: strong bounded no-label free-beam evidence, but still not a complete proof of solved OOD or a fully emergent rejection gate.

## 5. Key Findings

1. Forced path separates synthesis capability from routing failure. In v0.7.5, Path-Forcing Smoke Test（强制路径冒烟测试） reached exact match 1.0 while free beam remained 0.0.
2. Sub-beam regrowth can rescue paths missed by global beam. In v0.7.6, teacher and seeded free sub-beam diagnostics reached 1.0 in their diagnostic setting while global beam remained much weaker.
3. Direct global assimilation can cause negative transfer. In v0.7.7, global beam dropped from 0.2733 to 0.1 after broad assimilation.
4. Local root colonies are safer than direct global assimilation. v0.7.8 and v0.7.9 moved from global broadcast to keep-local and shadow-only lifecycle mechanisms.
5. Scaling improves global beam but not OOD toxicity. v0.8.0 large improved global beam to 0.5017, while OOD toxicity stayed around 0.67.
6. OOD false accept is strongly linked to canonicalization / guard ambiguity. v0.8.1 identified canonicalizer_made_it_look_supported as the most common false accept reason.
7. Shadow promotion is useful as a safety mechanism before real promotion. v0.7.9 through v0.8.1.1 kept real promotion disabled while measuring likely effects.

### Finding: Scale-Induced Routing Signal Was Reproduced

The v0.8 scale signal is no longer merely an unverified overnight artifact. v0.8.0/v0.8.1 large reached global beam 0.5017. v0.8.1.1 xlarge same-seed reached 0.8167, and alternate-seed/light reached 1.0. Metric consistency passed, inconsistency_count was 0, and split mismatch was explained as dataset_capacity.

Limits: this finding is bounded by dataset capacity, controlled arithmetic / TargetIR setting, no full/longrun completion, no same-size LLM comparison, and no proof of stable convergence.

### Finding: Boundary Rejection Signal Survived No-Label Free-Beam Evaluation

v0.8.6 showed training-probe boundary improvement. v0.8.7 removed boundary labels and answer fields from inference, passed the no-label guard with zero forbidden field access, passed held-out leakage checks, and kept the free-beam boundary metrics perfect under the tested probe criteria. This strengthens the Boundary-Aware Curriculum（边界感知数据课程） hypothesis.

Limits: this is still a bounded probe, not external OOD, not persisted router-state replay, not same-size LLM baseline, and not safe real promotion.

## 6. Failure Analysis

JianMu v0.8 still has several unresolved failures:

- Candidate-space failure（候选空间失败） remains high in many free-beam runs, even after forced path proves synthesis capability.
- Ranking failure（排序失败） is not the dominant diagnosis in the cited v0.7.3-v0.7.5 records; candidate absence and routing weakness dominate.
- OOD false accept（分布外误接收） remains a major bottleneck.
- The canonicalizer can make some OOD inputs look supported, which requires a canonicalization-aware guard rather than removing canonicalization.
- Global Assimilation（全局吸收） caused negative transfer in v0.7.7.
- Promotion candidates remain absent or unaccepted under strict shadow promotion gates.
- There is no stable convergence proof, no optimal code generation proof, and no claim that arithmetic is solved.

### Remaining Risks After v0.8.1.1

- OOD pollution risk remains true.
- Full and longrun modes were not completed.
- Real promotion remains disabled.
- Same-size LLM and Transformer comparisons are missing.
- Compiler/runtime efficiency objectives are not yet included.
- Generated code optimality is not optimized.

### Remaining Risks After v0.8.7

- Free-beam success may still depend on the probe scaffold.
- Real persisted router/root state must be tested.
- External held-out OOD is required.
- More seeds are required.
- Larger-scale free-beam runs are required.
- Same-size LLM / Transformer baselines are still missing.
- Dataset artifact strategy remains necessary for larger scales.

## 7. Theoretical Hypothesis: Set-Theoretic Routing Topology

This section is hypothesis / future work, not an experimental claim.

The current repository snapshot used for this draft does not contain a local `JIANMU_SET_THEORETIC_ROUTING.md` file. The following is therefore treated as a future hypothesis only:

- Subset relations may define lower-layer branches.
- Mutually exclusive concepts may compete at the same layer.
- Incomparable overlapping sets may require independent entry trees.
- Canonicalization and OOD guard may need to preserve set boundaries rather than only surface similarity.

These ideas are not yet empirically proven in JianMu v0.8.

## 8. Limitations

- JianMu v0.8 is evaluated on a small controlled arithmetic-centered domain.
- It does not prove general program synthesis.
- It does not enable real promotion yet.
- OOD toxicity remains high and is not solved by scale alone.
- Scale experiments are bounded by runtime.
- Full and longrun modes remain uncompleted.
- Compiler correctness is limited to generated test programs and sandboxed checks.
- Current results optimize for compiler-verifiable correctness / TargetIR routing coverage, not optimal code generation.
- The system currently finds valid routes, not necessarily shortest or fastest generated programs.
- Same-size LLM and Transformer baselines are not yet included.
- There is no code efficiency objective yet.
- Generated code performance is not optimized.
- The canonicalizer is an engineering normalization layer, not a TargetIR parser.
- v0.8.7 is a no-label free-beam probe, not a full production inference benchmark.
- OOD solved is not claimed.
- A fully emergent rejection gate is not claimed.
- Same-size LLM advantage is not claimed.
- Safe real promotion is not claimed.
- Real persisted router-state evaluation is still required.


## 9. Future Work

- v0.8.2 Runtime Parallelism & Buffered Records（运行时并行与缓冲记录）.
- v0.8.3 Canonicalization-Aware OOD Guard（规范化感知分布外守卫）.
- v0.8.8 Real Persisted Router-State & External OOD Eval（真实持久化路由状态与外部分布外评估）.
- v0.8.9 / v0.9 Scaling Ladder: 3M / 10M / 30M（规模阶梯）.
- Same-size Transformer / LLM baseline（同体量 Transformer / LLM 基线）.
- 100M candidate run（亿级候选运行）.
- PDF export and arXiv technical report submission decision.
- v0.9 Scaling Ladder: 3M / 10M / 30M（规模阶梯）.
- v0.9.x Same-size LLM / Transformer baseline（同体量 LLM / Transformer 基线）.
- v1.0 100M candidate run + baseline comparison.
- Optional C/C++ hot-path runtime acceleration after Python reference is stable.
- Efficiency-aware fitness and generated code performance metrics.
- Set-theoretic routing topology validation.
- More explicit separation between canonicalization, OOD guard, routing, and synthesis failure.

## 10. Conclusion

JianMu v0.8 is a reproducible prototype of compiler-verified, nutrient-guided routing. Its strongest current evidence is diagnostic clarity, local sub-beam rescue, root lifecycle activation, and a reproduced bounded xlarge scale signal that improves global beam on supported samples.

The main unresolved bottlenecks are OOD toxicity, safe promotion, and global routing robustness. The v0.8.1.1 and v0.8.7 evidence supports continued work on runtime scale, persisted router-state evaluation, external OOD evaluation, canonicalization-aware OOD guard, and strict shadow promotion, not claims of stable convergence, solved arithmetic, solved OOD, same-size LLM advantage, safe real promotion, or general program synthesis.

## Local Record References

- `records/v0_5_7/route_classifier_metrics.json`
- `records/v0_5_8/arithmetic_targetir_metrics.json`
- `records/v0_6_8/large_dataset_smoke_metrics.json`
- `records/v0_6_9/large_training_probe_metrics.json`
- `records/v0_7_3/wide_beam_backtracking_metrics.json`
- `records/v0_7_5/capability_alignment_metrics.json`
- `records/v0_7_6/rootfork_metrics.json`
- `records/v0_7_7/rootfork_global_metrics.json`
- `records/v0_7_8/nutrient_zone_metrics.json`
- `records/v0_7_9/colony_activation_report.md`
- `records/v0_8_0/colony_scale_stress_report.md`
- `records/v0_8_1/ood_toxicity_longrun_report.md`
- `records/v0_8_1_1/mainline_conclusion.md`
- `records/v0_8_1_1/metric_reconciliation_report.md`
- `records/v0_8_1_1/xlarge_reproduction_summary.json`

## v0.8.7 Local Record References（本地记录引用）

- `records/v0_8_7/mainline_conclusion.md`
- `records/v0_8_7/freebeam_boundary_report.md`
- `records/v0_8_7/no_label_inference_guard.json`
- `records/v0_8_7/boundary_generalization_metrics.json`
- `records/v0_8_6/boundary_training_report.md`
- `records/v0_8_5/boundary_dataset_report.md`
