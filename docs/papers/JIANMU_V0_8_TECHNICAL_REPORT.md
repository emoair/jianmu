# JianMu: Nutrient-Guided Root-Colony Routing for Compiler-Verified Program Synthesis

中文副标题：JianMu：一种面向编译器验证程序合成的养分引导根群路由系统

Report status: Technical Report Draft（技术报告草稿）, Not a formal paper yet（尚非正式论文）.

Record scope: This draft summarizes local repository evidence from v0.5.7 to v0.8.1. It cites repository documents and records only, and does not modify or reinterpret original experimental data.

This report does not claim stable convergence, general program synthesis, AGI, Transformer replacement, solved arithmetic, optimal code generation, or production readiness.

## Abstract

JianMu is a compiler-verified routing and synthesis prototype. It routes raw Chinese/math input through Canonical Symbol Layer（规范符号层）, BranchChain（分支链）, RootFork Sub-Beam Regrowth（根叉子束再生）, Nutrient-Zone Root Colony（养分区根群）, Toxic Nutrient（毒性养分） accounting, Shadow Promotion（影子晋升）, AtomicSynthesis（原子结构合成）, and Compiler Sandbox（编译器沙箱） validation.

The strongest v0.8 evidence is diagnostic rather than final: Path-Forcing Smoke Test（强制路径冒烟测试） separated AtomicSynthesis（原子结构合成） capability from routing failure; RootFork Sub-Beam Regrowth（根叉子束再生） rescued paths missed by global beam; Colony Nutrient Activation（根群养分激活） made local root lifecycle states observable; and Colony Scale Stress Probe（根群规模压力探针） showed scale-sensitive improvement in global beam. In v0.8.1, the large run kept global beam at 0.5017, found OOD false accept（分布外误接收） as the main bottleneck, and a rollback-safe guard candidate reduced OOD false accept from 0.335 to 0.235 while arithmetic retention stayed 1.0.

## 1. Introduction

Direct natural-language-to-code generation is difficult to inspect, difficult to reject safely, and difficult to roll back when a model follows the wrong semantic path. JianMu explores a different prototype direction: route input into TargetIR（目标中间表示）, synthesize from a structured path, and verify generated behavior with compiler/run feedback.

The goal is not to produce visually impressive code. The goal is to discover whether a verifiable path exists, whether the routing system can find it without reading answer labels during free evaluation, and whether failures can be localized to candidate generation, ranking, synthesis, OOD guard, or lifecycle resource limits.

## 2. System Overview

The current JianMu v0.8 line uses these components:

- Canonical Symbol Layer（规范符号层）: normalizes raw Chinese/math text into canonical_text（规范文本） and Source Map（源映射）. It does not emit TargetIR（目标中间表示） or C source.
- BranchChain（分支链）: proposes layered routing decisions.
- RootFork Sub-Beam Regrowth（根叉子束再生）: starts Prefix-Conditioned Sub-Beam（前缀条件子束） search near weak fork points.
- Nutrient-Zone Root Colony（养分区根群）: groups rescued paths into local Nutrient Zones（养分区） and local Root Colonies（根群） instead of broadcasting them globally.
- Toxic Nutrient（毒性养分）: treats OOD false accept（分布外误接收） and unsupported false accept as negative lifecycle feedback.
- Shadow Promotion（影子晋升）: evaluates proposed colony influence on a shadow copy before any real promotion. Real promotion remains disabled in the v0.8.1 evidence summarized here.
- AtomicSynthesis（原子结构合成） and Compiler Sandbox（编译器沙箱）: generate TargetIR（目标中间表示） from BranchPath（分支路径） and validate generated programs through compile/run checks.

Free-Beam Evaluation（自由束评测） does not read target_branch_path, target_ir, or expected_output. Teacher-Guided Diagnostic（教师引导诊断） may use those labels only after generation for diagnosis, reward construction, and offline path-forcing audits.

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

Result: v0.8.0 completed small/medium/large scale stress runs. Large global_correct_targetir_in_beam_rate reached 0.5017, candidate_space_failure_rate fell to 0.4983, and stable roots increased with scale. However OOD toxicity stayed near 0.67. v0.8.1 completed the large OOD toxicity long-run probe. Its most common false accept reason was canonicalizer_made_it_look_supported, and a guard candidate reduced OOD false accept from 0.335 to 0.235 without lowering arithmetic retention or global beam.

Failure discovered: scale helped supported routing more than OOD rejection. OOD guard ambiguity is now a primary bottleneck.

Next response: v0.8.2 should focus on canonicalization-aware OOD guard rather than real promotion.

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

| Version | Experiment | Dataset / Sample Count | Key Metrics | Conclusion | Non-Claim |
|---|---:|---:|---|---|---|
| v0.8.0 | Colony Scale Stress Probe（根群规模压力探针） | small/medium/large completed | global beam: small 0.2933, medium 0.2733, large 0.5017; OOD toxicity near 0.67 | Scale improved global beam and stable roots | Scale did not solve OOD toxicity |
| v0.8.1 | OOD Toxicity Stress & Long-Run Scale Probe（分布外毒性压力与长时规模探针） | large completed; xlarge/full skipped | OOD false accept 0.335 to 0.235 after guard; arithmetic retention 1.0; global beam 0.5017 unchanged | OOD guard candidate improved rejection without hurting retention | Does not prove stable OOD handling |

## 5. Key Findings

1. Forced path separates synthesis capability from routing failure. In v0.7.5, Path-Forcing Smoke Test（强制路径冒烟测试） reached exact match 1.0 while free beam remained 0.0.
2. Sub-beam regrowth can rescue paths missed by global beam. In v0.7.6, teacher and seeded free sub-beam diagnostics reached 1.0 in their diagnostic setting while global beam remained much weaker.
3. Direct global assimilation can cause negative transfer. In v0.7.7, global beam dropped from 0.2733 to 0.1 after broad assimilation.
4. Local root colonies are safer than direct global assimilation. v0.7.8 and v0.7.9 moved from global broadcast to keep-local and shadow-only lifecycle mechanisms.
5. Scaling improves global beam but not OOD toxicity. v0.8.0 large improved global beam to 0.5017, while OOD toxicity stayed around 0.67.
6. OOD false accept is strongly linked to canonicalization / guard ambiguity. v0.8.1 identified canonicalizer_made_it_look_supported as the most common false accept reason.
7. Shadow promotion is useful as a safety mechanism before real promotion. v0.7.9 through v0.8.1 kept real promotion disabled while measuring likely effects.

## 6. Failure Analysis

JianMu v0.8 still has several unresolved failures:

- Candidate-space failure（候选空间失败） remains high in many free-beam runs, even after forced path proves synthesis capability.
- Ranking failure（排序失败） is not the dominant diagnosis in the cited v0.7.3-v0.7.5 records; candidate absence and routing weakness dominate.
- OOD false accept（分布外误接收） remains a major bottleneck.
- The canonicalizer can make some OOD inputs look supported, which requires a canonicalization-aware guard rather than removing canonicalization.
- Global Assimilation（全局吸收） caused negative transfer in v0.7.7.
- Promotion candidates remain absent or unaccepted under strict shadow promotion gates.
- There is no stable convergence proof, no optimal code generation proof, and no claim that arithmetic is solved.

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
- Compiler correctness is limited to generated test programs and sandboxed checks.
- There is no code efficiency objective yet.
- Generated code performance is not optimized.
- The canonicalizer is an engineering normalization layer, not a TargetIR parser.

## 9. Future Work

- v0.8.2 canonicalization-aware OOD guard.
- v0.9 stable colony promotion gate.
- v1.0 reproducible release package.
- Larger and more diverse datasets.
- Efficiency-aware fitness and generated code performance metrics.
- Set-theoretic routing topology validation.
- More explicit separation between canonicalization, OOD guard, routing, and synthesis failure.

## 10. Conclusion

JianMu v0.8 is a reproducible prototype of compiler-verified, nutrient-guided routing. Its strongest current evidence is diagnostic clarity, local sub-beam rescue, root lifecycle activation, and a scale signal that improves global beam on supported samples.

The main unresolved bottlenecks are OOD toxicity, safe promotion, and global routing robustness. The v0.8.1 evidence supports continued work on canonicalization-aware OOD guard and strict shadow promotion, not claims of stable convergence or solved program synthesis.

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
- `records/v0_7_9/colony_activation_metrics.json`
- `records/v0_8_0/colony_scale_stress_metrics.json`
- `records/v0_8_1/ood_toxicity_longrun_metrics.json`
