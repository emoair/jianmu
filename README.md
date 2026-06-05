## v1.0.4 Development Direction

v1.0.4 explores CSystems Frontier Substrate Probe. After v1.0.3.1 validated classic algorithm variants, this version tests controlled C systems features including pointer basics, malloc/free lifecycle, sandboxed file IO, multi-file compile/link, and simple struct patterns. This is not arbitrary project parsing, not production support, not memory-safety proof, and not a formal proof of Turing completeness.

## v1.0.3.1 Development Direction

v1.0.3.1 explores ForgeCorpus Algorithm Variant Scale Probe. After v1.0.3 introduced deterministic classic C algorithm families, this version adds requirement-driven variants such as variable renaming, function renaming, array-size changes, loop-direction changes, boundary-value changes, sorting-order changes, helper-function splitting, and recursion base-case variants. It also audits metric freshness and sample accounting to ensure the algorithm evidence is fresh and not inherited from earlier summaries.

## v0.9.3.1 Development Direction

v0.9.3.1 audits the v0.9.3 arithmetic positive signal. It checks metric provenance, forbidden-field leakage, heldout group separation, baseline/ablation evidence, and failure examples. It does not introduce new architecture claims and does not claim solved arithmetic.

## v0.9.15.1 Development Direction

v0.9.15.1 re-audits a multi-agent raw LLM draft dataset after v0.9.15 showed severe template collapse and duplication. It treats the raw dataset as untrusted input, measures multi-agent collapse, duplicate and leakage rates, support-status safety, conversion success, and real MSVC compiler verification. The version does not promote raw data directly into training and does not claim Turing completeness.

## v0.9.15.2 Development Direction

v0.9.15.2 replaces unreliable raw LLM free generation with a Codex/grammar-driven Chinese data factory. Current-supported training inputs are restricted to Chinese, while English and mixed-language samples are treated as boundary, hard-OOD, future multilingual, or review cases. The version generates deterministic Chinese bounded-control data, audits language-domain safety, verifies supported samples with real MSVC compiler checks, and compares the result against the failed raw LLM generation path. It does not claim Turing completeness or solved program synthesis.

## v0.9.16 Development Direction

v0.9.16 reruns training with the audited v0.9.14 Turing-frontier dataset v2 and the v0.9.15.2 Codex/grammar Chinese dataset. Only Chinese current-supported bounded-control samples enter train_current; function, array, recursion, unbounded execution, English, and mixed-language samples remain boundary/future/review data. The version compares dataset_v2_only, chinese_factory_only, and mixed data profiles under the layerwise sparse 1B freeze-prune profile, with compiler validation and historical regression checks. It does not claim Turing completeness or function/array/recursion support.

## v0.9.26.1 Development Direction

v0.9.26.1 reruns the Turing frontier with a true wall-clock endurance rule: at least 12 hours are required before the endurance run can be marked complete. It analyzes frontier failures, generates RedQueen repair assignments, scales unbounded while / recursion / state-growth frontier training, and strengthens compiler/watchdog validation. This remains finite experimental evidence, not a formal proof of Turing completeness.

## v0.9.27 Development Direction

v0.9.27 adds an MSVC frontend syntax-filter protocol for faster training-time screening, followed by batch full-compile validation after training. It also scales function definitions/calls, fixed-array operations, function-array interop, and adds a constructive Turing expressivity proof artifact. Syntax filtering is not treated as correctness evidence; final validation remains full compile/run/stdout or watchdog-based verification.

## v0.9.27.1 Development Direction

v0.9.27.1 analyzes the batch full-compile failures from v0.9.27, replays wrong-stdout and timeout cases, builds RedQueen repair assignments, generates a targeted repair dataset, and reruns full compile validation. The goal is to restore compiler-clean evidence without adding production support, changing runtime boundaries, or treating syntax filtering as correctness evidence.

## v0.9.17 Development Direction

v0.9.17 introduces the RedQueen Curriculum Engine and HydraBudget Allocator. RedQueen mines failures from v0.9.16 and generates verifier-checked Chinese adversarial curriculum data for weak bounded-control stages. HydraBudget runs a shadow adaptive layerwise budget policy that expands only when utilization, candidate-miss contribution, marginal gain, and safety gates justify it, with rollback on regression. This version keeps current-supported boundaries unchanged and does not claim Turing completeness or function/array/recursion support.

# JianMu MVP

JianMu v0.5 is a Chinese-first hierarchical semantic routing runtime for
compiler-validated deterministic program rewriting.

## v0.9.1 Development Direction

v0.9.1 explores Large-Scale Full-State Reproduction & Baseline Harness（大规模完整状态复验与基线框架）. It scales the v0.9.0 `full_router_root` runtime capture result to larger modes, expands external OOD evaluation, increases seed coverage, profiles runtime/state size, and introduces baseline/ablation harnesses. It does not claim solved OOD, solved arithmetic, same-size LLM advantage, or safe real promotion.

Author: Huang Linquan (空气)

## v0.9.1.1 Development Direction

v0.9.1.1 performs a Real Workload Audit（真实工作负载审计） of v0.9.1. It checks whether the reported xlarge fullstate, expanded OOD, baseline, and ablation results came from actual per-sample execution or from harness/probe summary paths. It also adds workload tracing, sample counters, cross-process execution tracing, baseline/ablation traces, runtime anomaly diagnosis, and a small real-workload sanity rerun. It does not introduce new architecture claims.

## v0.9.1.2 Development Direction

v0.9.1.2 performs a Real Longrun With Mandatory Counters（带强制计数器的真实长跑验证）. After v0.9.1.1 downgraded v0.9.1 to harness/probe summary evidence, this version runs real per-sample workloads with workload traces, mandatory counters, cross-process child eval traces, real baseline/ablation execution traces, and runtime plausibility checks. It does not introduce new architecture claims.

## v0.9.2 Development Direction

v0.9.2 builds an Arithmetic Curriculum Dataset（四则运算课程数据集） for future compiler-verified arithmetic synthesis probes. It separates current-supported integer arithmetic from unsupported arithmetic boundaries, true-false-accept traps, future-domain candidates, near-OOD arithmetic, hard OOD, and review samples. This dataset-only version does not train the model and does not claim solved arithmetic.

---

## Language Scope (v0.5)

JianMu v0.5 is a **Chinese-first deterministic program rewriting runtime**.

Current natural-language input support is intentionally limited to Chinese.
English is not a natural-language interface target at this stage. C language
keywords and technical tokens such as `C`, `int`, `printf`, `main`, `return`,
and variable names like `a`, `b`, `c` are still supported when they appear in
Chinese-first input.

Supported examples include:

- `写一个 C 程序，输出 1+2+3`
- `定义三个 int，分别是 1、2、3，然后 printf 输出和`
- `再加一个二`

Pure English natural-language inputs such as `sum of three numbers` are reported
as unsupported instead of being guessed.

---

## v0.3 → v0.4 → v0.5

**JianMu v0.3** proved that `ProgramIR + Expert + CEmitter + C compiler Sandbox` works as an execution scaffold.

**JianMu v0.4** adds speculative routing: a single input no longer maps directly to one path.
Instead, multiple `RouteCandidate` are generated, each compiled and executed, and the winner
is selected by execution feedback — not by the rule router.

**JianMu v0.5** adds Chinese-first hierarchical semantic neurons and
`expected_output_provenance`, so route candidates carry auditable semantic
features and cannot self-certify correctness from untrusted generated outputs.

```
v0.3:  input → single intent → single expert chain → compile/run
v0.4:  input → multiple RouteCandidate → parallel execution → feedback selects winner
                                                             → RouteMemory records experience
```

---

## Requirements

- Python 3.8+
- `gcc`, `clang`, or MSVC `cl.exe`
- `pytest` (`pip install pytest`)

Windows users can use any one of:

1. MSYS2 UCRT64 `gcc`
2. LLVM `clang`
3. Visual Studio Developer Command Prompt / Developer PowerShell with MSVC `cl.exe`

`cl.exe` usually needs to run from a Developer Command Prompt for VS or Developer PowerShell for VS. A normal PowerShell session may not find `cl`.

## Run demo

```bash
python examples/demo_sum.py
```

## Run tests

```bash
python -m pytest tests/ -v
```

---

## What v0.5 DOES prove

- Chinese-first input can be routed through a deterministic rewriting runtime
- Hierarchical semantic neurons can expose `SemanticFeatures` and `neuron_results`
- A rule router can be demoted from **final decision-maker** to **candidate generator**
- Multiple `RouteCandidate` paths can be generated from one input
- `ProgramIR`-based C generation can remain separate from routing
- Multiple expert chains can be executed speculatively and ranked by real compiler/runtime feedback
- Compiler sandbox validation can act as execution feedback
- `RouteMemory` can record route-level success/failure experience and influence future `prior_score`
- `TraceCache` (result cache) and `RouteMemory` (path experience) serve distinct roles
- The winner is always selected by `correctness_score == 1.0`, never by prior alone
- `expected_output_provenance` prevents candidates with untrusted expected outputs from self-certifying
- Unsupported English natural-language input is rejected instead of guessed

## What v0.5 does NOT prove

- **True natural language understanding** — `SpeculativeRouter` is still rule-based candidate generation
- **Multilingual natural-language understanding** — English natural-language input is out of scope in v0.5
- **Learned routing** — no statistical or neural route selection
- **General code intelligence** — domain is still C integer summation only
- **Scalability** beyond this minimal domain
- **A replacement for LLMs or compilers**
- **AGI or general program synthesis**
- **BPU hardware co-design**

---

## License

JianMu is licensed under the GNU Affero General Public License v3.0 only
(`AGPL-3.0-only`).

Open-source and commercial use are permitted under the `AGPL-3.0-only` terms,
provided that derivative works and network-accessible modified versions comply
with the AGPL source disclosure requirements.

Proprietary or closed-source commercial use requires a separate commercial
license from the author.

This is not a ban on commercial use; it is a strong copyleft license with an
optional commercial dual-licensing path.

## Author

Author: Huang Linquan (空气)

---

## Known limitations (v0.5)

1. Candidate generation is still handcrafted and rule-based, not learned.
2. Only a small fixed set of candidate routes exists in the current summation/editing domain.
3. `_situation_key` uses coarse operation-class hashing, not true semantic similarity.
4. `CEmitter` is still string-based, not AST-level rewriting.
5. Non-addition expressions such as `1-2`, `1*2`, and `1/2` are intentionally unsupported in v0.5.
6. Limited negative literal cases are supported, but systematic arithmetic expression parsing is not.
7. The system does not yet demonstrate scalability beyond this minimal domain.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Hierarchical Router](docs/HIERARCHICAL_ROUTER.md)
- [Speculative Routing](docs/SPECULATIVE_ROUTING.md)
- [Evaluation](docs/EVALUATION.md)
- [Non-Claims](docs/NON_CLAIMS.md)
- [Archived early planning notes](docs/archive/)
- [Red-team critique](CRITIQUE.md)

## Development Notes

This artifact was developed with AI-assisted implementation and human-directed
red-team review.

All release claims are intentionally limited to reproducible tests,
compiler-backed validation, and documented non-claims. The current router is a
handcrafted semantic scaffold, not a learned model.

## v0.5.5 Development Experiment

A small prefix-evolution prototype is being explored under
`jianmu/self_learning/`. It trains stateless prefix neurons to emit ProgramIR
tokens under oracle supervision and compiler-backed validation. This is not part
of the v0.5 release claims.

v0.5.6 development branch adds a controlled Chinese intent-to-structure dataset
seed for future self-learning and learned-router experiments.

v0.5.8 development branch explores a 1M-parameter hashed routing baseline for
Chinese-first arithmetic TargetIR regeneration. It predicts canonical arithmetic
structure, not C source text.

## v0.5.9 Development Direction

v0.5.9 introduces a BranchChain Training Charter and a toy branch-chain training
scaffold. It corrects the direction from flat label classification toward
layered branch decisions, path-level reward, and Canonical TargetIR
regeneration. This is a development experiment, not a v0.5 release claim.

## v0.6 Development Direction

v0.6 development introduces a minimal DarwinForge scaffold that connects
BranchChain candidate generation, AtomicSynthesis TargetIR construction,
compiler-backed validation, and path-level evolutionary fitness. It is a
development experiment and not a v0.5 release claim.

## v0.6.1 Development Direction

v0.6.1 explores BranchChain curriculum freezing: early routing layers are
trained first, frozen after stability criteria are met, and kept active during
downstream routing while later layers continue learning. This is a
training-dynamics experiment, not a v0.5 release claim.

## v0.6.2 Development Direction

v0.6.2 explores Layerwise Highest-Stable Threshold Search（分层最高稳定冻结阈值搜索） for
BranchChain（分支链） curriculum training. Each layer starts from a high freeze
threshold（冻结阈值） and gradually anneals downward（向下退火） only when stalled,
freezing at the highest threshold it can stably satisfy.

## v0.6.3 Development Direction

v0.6.3 explores Confidence-Gated Guarded BranchChain（置信度守卫式带守卫分支链）.
Instead of relying on a single SupportGate（支持/拒绝门）, each routing layer can
stop early when no sufficiently confident continuation branch exists. Rejection
becomes a natural no-confidence early stop, not a source-code patch or hardcoded
parser rule.

## v0.6.4 Development Direction

v0.6.4 explores an Architecture-Aligned Dataset（架构对齐数据集） where multiple
Chinese natural-language descriptions（中文自然语言描述）, pure math expressions（纯数学表达）,
and Chinese technical mixed inputs（中文技术混合输入） map to the same TargetIR（目标中间表示）.
This corrects earlier toy labels where implicit C（隐式 C） inputs were incorrectly
treated as unknown language（未知语言）.

## v0.6.5 Development Direction

v0.6.5 explores Paraphrase-Invariant TargetIR Training（复述不变目标中间表示训练）.
Multiple Chinese natural-language descriptions（中文自然语言描述）, Chinese technical
mixed inputs（中文技术混合输入）, and pure math expressions（纯数学表达） in the same
Paraphrase Group（复述组） are evaluated for convergence toward the same TargetIR（目标中间表示）.

## v0.6.6 Development Direction

v0.6.6 explores Hindsight Branch Re-Ranking（回看式分支重排） and Group Beam
Selection（组级束搜索）. Instead of discarding non-winner candidates immediately,
JianMu keeps top-k BranchPath（分支路径） candidates, evaluates them with
TargetIR（目标中间表示） and Paraphrase Group（复述组） feedback, then promotes
Correct-Low-Score Candidate（低分正确候选） paths and downranks
Wrong-High-Score Candidate（高分错误候选） shortcuts.

## v0.6.7 Development Direction

v0.6.7 explores Perfect-Layer Backtracking Curriculum（完美层回溯课程训练）
for toy/synthetic BranchChain（分支链） training. Each layer attempts to reach
perfect accuracy（完美准确率） before freezing. If a Downstream Layer（下游层） stalls,
Upstream Layer（上游层） entries can be conditionally unfrozen（条件解冻） and jointly
retrained. The 100% rule is only for toy/synthetic deterministic data（玩具/合成确定性数据）.

## v0.6.8 Development Direction

v0.6.8 introduces a Large Architecture-Aligned Dataset（大规模架构对齐数据集）
and Scale Smoke Benchmark（规模化冒烟基准）. The dataset is generated locally
and deterministically, expanding Chinese natural-language descriptions（中文自然语言描述）,
Chinese technical mixed inputs（中文技术混合输入）, pure math expressions（纯数学表达）,
Paraphrase Groups（复述组）, and OOD Evaluation（分布外评测） while avoiding English
natural-language positive training samples（英语自然语言正样本）.

## v0.6.9 Development Direction

v0.6.9 explores a Large Dataset Full Training Probe（大数据集全量训练探针）
over the v0.6.8 Large Architecture-Aligned Dataset（大规模架构对齐数据集）.
It scales population_per_layer（每层种群数量）, top_k_candidates（候选保留数量）,
and generations（训练代数）, then reports Full-Split Evaluation（全切分评测）
and Stratified Evaluation（分层评测） by input mode（输入模式）, expression
family（表达式族）, and OOD behavior（分布外行为）.

## v0.7.0 Development Direction

v0.7.0 begins Symbol Grounding Curriculum（符号接地课程）. It studies whether
BranchChain（分支链） and AtomicSynthesis（原子结构合成） can learn Chinese numeral
symbols（中文数字符号） and operator words（运算词） from paired paraphrase
groups（成对复述组） and TargetIR（目标中间表示） feedback, without hardcoding Chinese
numeral parsing（中文数字解析） or operator mapping（运算符映射） into inference.

## v0.7.1 Development Direction

v0.7.1 introduces a Canonical Symbol Layer（规范符号层） before BranchChain（分支链）.
It normalizes Chinese numerals（中文数字） and operator words（运算词） into canonical
text（规范文本）, such as “三加二” → “3+2”, while preserving Source Map（源映射）.
The layer does not generate TargetIR（目标中间表示） or C source; it only standardizes
equivalent input symbols before routing and synthesis.

## v0.7.2 Development Direction

v0.7.2 explores Canonicalized Training Probe（规范化输入训练探针）. It compares Raw
Input Training（原始输入训练） with Canonical Input Training（规范输入训练） by routing
canonical_text（规范文本） from the Canonical Symbol Layer（规范符号层） into
BranchChain（分支链） while preserving raw_text（原始文本） and Source Map（源映射）
for evaluation.

## v0.7.3 Development Direction

v0.7.3 explores Wide-Beam Backtracking Search（宽束回溯搜索） under canonicalized
input（规范化输入）. It combines Wide Branch Beam Search（宽束分支搜索） with
Conditional Upstream Unfreeze（条件上游解冻） and Layer Clone Perturbation（层克隆扰动）.
Instead of freezing layers too early, JianMu keeps wider BranchPath（分支路径）
ensembles, lets complete paths reach TargetIR（目标中间表示）, then uses Full Path
Diagnostics（完整路径诊断） to decide whether failure is caused by candidate-space
absence（候选空间缺失）, ranking failure（排序失败）, upstream boundary failure（上游边界失败）,
or synthesis failure（合成失败）.

## v0.7.4 Development Direction

v0.7.4 introduces RootForge Growth Dynamics（根铸生长动力学）. It repairs
candidate-space gaps such as literal-only TargetIR（字面量目标中间表示） and selected
precedence patterns（优先级结构）, then explores Nutrient-Guided Regrowth（养分引导再生）,
Root Necrosis（根系坏死）, Nutrient Contrast（养分对比）, and Annealed Pruning（退火枝剪）
over canonicalized BranchChain（规范化分支链） paths.

## v0.7.5 Development Direction

v0.7.5 focuses on RootForge Capability Alignment（根铸能力对齐）. It repairs
BranchChain（分支链） priors for Literal-Only TargetIR（单字面量目标中间表示）,
fixes negative-number routing（负数路由）, adds Path-Forcing Smoke Test（强制路径冒烟测试）,
and separates router candidate failure（路由候选失败） from AtomicSynthesis capability
failure（原子结构合成能力失败）.

## v0.7.6 Development Direction

v0.7.6 introduces RootFork Sub-Beam Regrowth（根叉子束再生）. After v0.7.5 proved that supported samples are synthesizable under forced BranchPath（强制分支路径）, this version diagnoses which layer assigns low score or prunes the correct option, then starts Prefix-Conditioned Sub-Beam（前缀条件子束） regrowth from that fork point. It also adds Path-Prior Seeding（路径先验播种）, OOD Guard Balancing（分布外守卫平衡）, and Scale Ladder（规模阶梯） diagnostics.

## v0.7.7 Development Direction

v0.7.7 explores RootFork Global Assimilation（根叉全局吸收）. It turns sub-beam rescued paths（子束救援路径） into global BranchChain（全局分支链） scoring updates, repairs Slot Binding（槽位绑定）, adds Root Lifecycle Manager（根生命周期管理器）, reconciles OOD Metrics（分布外指标）, and replaces the previous scale ladder with Real Scale Ladder（真实规模阶梯） runs.

## v0.7.8 Development Direction

v0.7.8 explores Nutrient-Zone Root Colony（养分区根群）. Instead of broadcasting sub-beam rescued paths（子束救援路径） into global BranchChain（全局分支链） weights, JianMu groups rescued paths into local Nutrient Zones（养分区）, lets nourished root tips（有养分根尖） proliferate locally, tracks Toxic Nutrient（毒性养分） such as OOD false accept（分布外误接收）, and only promotes stable low-toxicity colonies（低毒稳定根群） through small rollback-safe updates.

## v0.7.9 Development Direction

v0.7.9 explores Colony Nutrient Activation（根群养分激活）. After v0.7.8 created local Nutrient-Zone Root Colonies（养分区根群）, this version activates Local Nutrient Cycle（局部养分循环）, fixes Toxic Nutrient（毒性养分） accounting for OOD false accept（分布外误接收）, introduces Keep-Local Colony（保持局部根群）, and uses Shadow Promotion（影子晋升） instead of directly modifying global BranchChain（全局分支链） weights.

## v0.8.0 Development Direction

v0.8.0 explores Colony Scale Stress Probe（根群规模压力探针）. After v0.7.9 activated local colony lifecycle（局部根群生命周期）, this version runs larger shadow-only scale probes（只影子晋升的大规模探针） to determine whether JianMu is currently scale-limited（规模受限）, promotion-limited（晋升受限）, routing-limited（路由受限）, OOD-limited（分布外受限）, or resource-limited（资源受限）.

## v0.8.1 Development Direction

v0.8.1 explores OOD Toxicity Stress & Long-Run Scale Probe（分布外毒性压力与长时规模探针）. After v0.8.0 showed that larger scale improves global beam（全局束） and stable roots（稳定根）, this version analyzes OOD false accept（分布外误接收） by class, evaluates rollback-safe OOD guard candidates（可回滚分布外守卫候选）, and allows bounded hour-level xlarge/full runs without enabling real promotion（真实晋升）.

## v0.8.1.1 Development Direction

v0.8.1.1 performs Overnight Metric Reconciliation & XLarge Reproduction（过夜指标口径校验与 xlarge 复验）. After v0.8.1 overnight produced a strong xlarge signal, this version repairs test failures, reconciles before/after/guard metric definitions, diagnoses split mismatches, reruns xlarge with same and alternate seeds, and writes a Mainline Conclusion Ledger（主线结论账本）.

不要声称稳定收敛。
不要声称四则运算已攻破。
不要声称已经优于同体量 LLM。
## v0.8.2 Development Direction

v0.8.2 explores Runtime Parallelism & OOD Precision Audit（运行时并行与分布外精确审计）. After v0.8.1.1 confirmed the xlarge scale signal, this version adds 8-worker sample-level parallel execution（8 worker 样本级并行）, buffered records（缓冲记录）, runtime cache outside OneDrive（OneDrive 外运行缓存）, serial/parallel equivalence audit（串行/并行等价审计）, and OOD precision labeling（分布外精确标注） to distinguish true false accept（真正误接收） from near-OOD generalization candidates（近邻分布外泛化候选）.

不要声称稳定收敛。
不要声称四则运算已攻破。
不要声称已经优于同体量 LLM。

## v0.8.3 Development Direction

v0.8.3 explores High-Load Parallel Runtime & OOD Precision Recheck（高负载并行运行时与分布外精审复查）. After v0.8.2 added parallelism and buffered records scaffolds, this version benchmarks worker_count 1/2/4/8 under medium and xlarge-light workloads, allows project-local runtime cache when OneDrive sync is disabled, verifies serial/parallel metric equivalence, and rechecks OOD accepted samples to distinguish true false accept（真正误接收） from near-OOD generalization candidates（近邻分布外泛化候选）.

不要声称稳定收敛。
不要声称四则运算已攻破。
不要声称已经优于同体量 LLM。
## v0.8.4 Development Direction

v0.8.4 explores OOD Slice Replay & Generalization Boundary（分布外切片回放与泛化边界）. After v0.8.3 showed that accepted OOD samples include both true false accepts（真正误接收） and near-OOD generalization candidates（近邻分布外泛化候选）, this version replays the v0.8.1 OOD guard-stress slice, checks whether canonicalizer_made_it_look_supported（规范化器使输入看似受支持） can be reproduced, defines a supported boundary spec（支持边界规格）, and exports candidate datasets for supported expansion, future domains, and guard training.

不要声称稳定收敛。
不要声称四则运算已攻破。
不要声称 near-OOD 已经自动成为 supported success。

## v0.8.5 Development Direction

v0.8.5 explores Boundary-Aware Dataset Curriculum（边界感知数据课程）. After v0.8.4 showed that OOD accepted samples mostly fall into future-domain candidates（未来能力候选）, hard OOD（硬分布外）, and true false accept（真正误接收） rather than immediate supported expansion, this version builds a larger boundary-aware dataset with explicit nutrient/toxic pressure labels（养分/毒性压力标签） so rejection behavior can emerge from feedback rather than hard-coded rules.

不要声称稳定收敛。
不要声称四则运算已攻破。
不要声称 OOD 已解决。
不要声称拒绝门已完全自然涌现。

## v0.8.6 Development Direction

v0.8.6 explores Boundary Curriculum Training Probe（边界课程训练探针）. After v0.8.5 rebuilt the boundary-aware dataset ecology, this version tests whether nutrient/toxic pressure labels can improve rejection behavior without hard-coded rejection gates. It also introduces shard-aware dataset loading（分片感知数据加载） and dataset artifact policy（数据工件策略） to prepare for larger 10M/30M/100M scale runs.

不要声称稳定收敛。
不要声称四则运算已攻破。
不要声称 OOD 已解决。
不要声称拒绝门已经完全自然涌现，除非 emergent_rejection_signal_confirmed 为 true 且 supported retention 安全。

## v0.8.7 Development Direction

v0.8.7 explores Boundary Free-Beam Generalization Probe（边界自由束泛化探针）. After v0.8.6 showed strong boundary improvements under training-probe conditions, this version removes boundary labels from inference, evaluates held-out boundary slices under free-beam routing, and checks whether rejection behavior survives without hard-coded rejection gates or label leakage.

不要声称稳定收敛。
不要声称 OOD 已解决。
不要声称拒绝门完全自然涌现，除非 freebeam_emergent_rejection_signal_confirmed 为 true 且 no-label guard 通过。
## v0.8.8 Development Direction

v0.8.8 explores Real Persisted Router-State & External OOD Eval（真实持久化路由状态与外部分布外评估）. After v0.8.7 showed no-label free-beam boundary behavior on held-out slices, this version saves and reloads router/probe state, evaluates reloaded no-label free-beam behavior, adds external OOD slices, checks multi-seed stability, and reports whether the project is ready for a conservative arXiv technical report.

不要声称稳定收敛。
不要声称 OOD 已解决。
不要声称同体量 LLM 优势。
不要声称 safe real promotion。

## v0.8.9 Development Direction

v0.8.9 explores Full Router/Root State Persistence & Reloaded Boundary Eval（完整路由/根状态持久化与重载边界评估）. After v0.8.8 showed strong summary-only reload, external OOD, and multi-seed results but was blocked by summary-only persisted state, this version inventories real router/root state, serializes full router/root state where available, runs same-process and cross-process reload evaluation, checks forbidden fields, and updates arXiv readiness.

不要声称稳定收敛。
不要声称 OOD 已解决。
不要声称同体量 LLM 优势。
不要声称 safe real promotion。

## v0.9.0 Development Direction

v0.9.0 explores Runtime Training-State Capture & Paper Figure Data Pack（运行时训练状态捕获与论文图表数据包）. After v0.8.9 showed that the remaining blocker was partial persisted state rather than boundary behavior, this version captures trained BranchChain population, Root Colony state, lifecycle state, and nutrient/toxic memory during training, then tests full-state reload under no-label free-beam and external OOD. It also generates paper-ready figure data and matplotlib figures from records.

不要声称稳定收敛。
不要声称 OOD 已解决。
不要声称同体量 LLM 优势。
不要声称 safe real promotion。
## v0.9.3 Development Direction

v0.9.3 runs an Arithmetic Training Probe on the v0.9.2 arithmetic curriculum dataset. It evaluates whether JianMu can improve supported arithmetic candidate-space formation under no-label free-beam evaluation while preserving boundary rejection for unsupported arithmetic, traps, future-domain candidates, near-OOD arithmetic, and hard OOD. It does not claim solved arithmetic.

## v0.9.3.2 Development Direction

v0.9.3.2 performs a Non-Periodic Arithmetic Rerun. After v0.9.3.1 found that the v0.9.3 arithmetic gain could be explained by a deterministic index-period rule, this version reruns arithmetic evaluation with per-sample candidate traces, no periodic success rule, no fixed metric gain, baseline/ablation checks, and boundary safety checks. It does not claim solved arithmetic.

## v0.9.4 Development Direction

v0.9.4 performs a Real Compiler Arithmetic Spot Audit. It checks whether the v0.9.3.2 non-periodic arithmetic signal, previously verified under an internal evaluator, can be validated through real C compiler subprocesses where available. If no compiler is available, it reports the fallback backend honestly and does not claim compiler-backed verification.

## v0.9.4.2 Development Direction

v0.9.4.2 performs a Compiler Failure Taxonomy for the 45 failed samples in v0.9.4.1. It separates compiler/toolchain failures, C source generation issues, runtime errors, wrong outputs, unsafe-expression blocks, and trace errors. Original compiler-backed metrics are preserved; any patched rerun is reported separately. It does not claim solved arithmetic.

## v0.9.4.3 Development Direction

v0.9.4.3 performs a fresh compiler-backed reproduction of the v0.9.4.2 patched arithmetic result. It uses new samples and fresh MSVC compiler invocations to distinguish fresh reproduction from patched replay. It preserves the C token-spacing fix, tracks overlap with the original 600-sample audit, and does not claim solved arithmetic.

## v0.9.5 Development Direction

v0.9.5 performs a Full Compiler-Backed Arithmetic Longrun Probe. After v0.9.4.3 reproduced the arithmetic signal on fresh MSVC-compiled samples, this version scales the audit to larger fresh samples with real cl.exe invocations, checkpointed traces, boundary guards, latency profiles, and failure taxonomy. It does not claim solved arithmetic or Turing completeness.

## v0.9.5.1 Development Direction

v0.9.5.1 performs a Compiler Concurrency Scaling Probe. After v0.9.5 established a bounded real MSVC compiler-backed arithmetic longrun, this version measures how cl.exe concurrency affects throughput, latency, timeout rate, process-spawn stability, trace integrity, and boundary safety. It does not claim solved arithmetic or Turing completeness.

## v0.9.6 Development Direction

v0.9.6 builds a Turing Substrate Curriculum Dataset（图灵完备底座课程数据集） after the compiler-backed arithmetic longrun line. It introduces audited curriculum data for variables, assignments, sequences, if/else, bounded loops, and boundary/future-domain program samples. It also runs a 16-worker MSVC compiler validation spot using the tuned concurrency from v0.9.5.1. This version does not claim Turing completeness.

## v0.9.7 Development Direction

v0.9.7 runs a Bounded Substrate Training Probe（有界程序底座训练探针） on the v0.9.6 turing-substrate curriculum dataset. It evaluates whether JianMu can improve candidate-space formation for variables, assignments, sequences, if/else, bounded loops, and nested bounded control under no-label free-beam evaluation and real MSVC compiler validation. It does not claim Turing completeness.
## v0.9.7.1 Development Direction

v0.9.7.1 audits the v0.9.7 bounded substrate positive signal and attempts a full-level rerun on the large v0.9.6 substrate dataset. It also runs a bounded-substrate compiler worker scaling check for 8/16/32/64 MSVC cl.exe workers. The version keeps Turing-completeness and solved-program-synthesis claims out of scope.

## v0.9.7.2 Development Direction

v0.9.7.2 performs a compiler PermissionError failure taxonomy for the v0.9.7.1 bounded substrate full-level rerun. It diagnoses MSVC/Windows temporary-file and process-lifecycle failures, preserves the original v0.9.7.1 metrics, reports patched replay separately, and runs an independent compiler validation rerun after any temp/process management fix. It does not claim Turing completeness or solved program synthesis.

## v0.9.7.3 Development Direction

v0.9.7.3 reruns independent bounded-substrate compiler validation from a clean MSVC-enabled environment after v0.9.7.2 explained the previous PermissionError failures as cleanup-stage engineering issues. It preserves the original v0.9.7.1 metrics and patched v0.9.7.2 replay results, and reports the clean independent validation separately. It does not claim Turing completeness or solved program synthesis.

## v0.9.8 Development Direction

v0.9.8 performs a larger bounded-substrate training rerun after v0.9.7.3 restored clean MSVC independent validation. It uses the v0.9.6 large substrate curriculum, real cl.exe compiler validation, full_router_root persistence, cross-process reload, and terminal progress reporting. The progress UI is observational only and does not replace JSON/JSONL records. This version does not claim Turing completeness or solved program synthesis.

## v0.9.8.1 Development Direction

v0.9.8.1 repairs the bounded substrate terminal progress reporting and diagnoses the v0.9.8 performance plateau. It separates candidate-miss, in-beam ranking, stage-specific, beam-size, and ablation-related bottlenecks while preserving the original v0.9.8 records. This version does not claim improved model capability, Turing completeness, or solved program synthesis.

## v0.9.9 Development Direction

v0.9.9 builds a Turing-frontier curriculum dataset and runs a candidate-space coverage scale probe after v0.9.8.1 identified candidate miss as the dominant bounded-substrate plateau cause. The dataset covers supported bounded-control programs and future-domain structures such as functions, arrays, recursion, and unbounded loops, while keeping unsupported structures out of train_current. The budget probe tests beam size, candidate budget, control-template budget, root expansion budget, and memory budget without changing JianMu’s core architecture. This version does not claim Turing completeness or solved program synthesis.

## v0.9.10 Development Direction

v0.9.10 performs a targeted candidate-space expansion rerun using the best diagnostic budget profile identified in v0.9.9: beam=64, candidate_budget=512, control_template_budget=xlarge, root_expansion=8x, and memory_budget=8x. The profile is treated as a controlled budget configuration rather than an architecture change. This version evaluates whether candidate-miss reduction reproduces on fresh samples while preserving boundary/future-domain safety and real MSVC compiler validation. It does not claim Turing completeness or solved program synthesis.

## v0.9.11 Development Direction

v0.9.11 runs a Hundred-Million State Budget Probe after v0.9.10 reproduced targeted candidate-space expansion. It treats “state budget” as auditable JianMu internal state capacity--candidate fragments, control-flow templates, root/sub-root expansion slots, failure-pattern memory, nutrient-toxic memory, and routing/scoring profiles--not as neural network parameters. The version tests baseline, 10M, 30M, and 100M budget profiles with memory guards, compiler validation, boundary/future safety checks, and honest materialization-level reporting. It does not claim Turing completeness, solved program synthesis, or emergence proven.

## v0.9.12 Development Direction

v0.9.12 runs a Billion-State Budget Upper Frontier Probe after v0.9.11 showed smooth positive scaling up to a 100M lazy-indexed state budget. It evaluates 300M, 600M, and 1B JianMu internal state budgets with memory guards, materialization-level reporting, access audits, boundary/future safety checks, and real MSVC compiler validation. The 1B budget is not a neural-network parameter count and is not assumed to be fully materialized. This version does not claim Turing completeness, solved program synthesis, or emergence proven.

## v0.9.12.1 Development Direction

v0.9.12.1 audits why the v0.9.12 1B lazy-indexed state budget has low active touch ratio. It separates tree-layer allocation imbalance from dataset/curriculum activation effects, future-domain quarantine coldness, and sampling imbalance. The version runs dataset-balanced resampling probes and access-aware reallocation diagnostics without changing JianMu's core architecture or promoting a new default profile. It does not claim Turing completeness or solved program synthesis.

## v0.9.12.2 Development Direction

v0.9.12.2 tests access-aware adaptive allocation and balanced sampling after v0.9.12.1 diagnosed a mixed allocation-and-dataset bottleneck. It evaluates a combined hot-rebalanced 1B + branch-activation-balanced profile and a layerwise sparse 1B freeze-prune diagnostic profile. Layerwise 1B means lazy-indexed logical budget per tree layer with active-access guards, not fully materialized parameters. This version does not promote a default profile and does not claim Turing completeness or solved program synthesis.

## v0.9.12.3 Development Direction

v0.9.12.3 diagnoses the non-clean MSVC compiler validation observed in v0.9.12.2 for the layerwise sparse 1B freeze-prune profile. It classifies compiler failures, replays failed samples, and performs a clean MSVC rerun with reduced-worker fallback if needed. This version preserves original v0.9.12.2 records and does not promote any profile or claim Turing completeness.

## v0.9.13 Development Direction

v0.9.13 runs a layerwise profile promotion probe after v0.9.12.3 restored clean compiler validation for the layerwise sparse 1B freeze-prune profile. The version treats the profile as a candidate default only in shadow mode, compares it against current_1B and combined profiles, and checks capability, boundary/future safety, compiler validation, persistence, resource overhead, and integrity gates. Real promotion remains disabled, and no default profile is changed.

## v0.9.14 Development Direction

v0.9.14 combines a layerwise default-profile dry-run with Turing-frontier dataset v2 audit. The layerwise sparse 1B freeze-prune profile is loaded through a shadow default path, but real promotion remains disabled and the actual default profile is not changed. The version also builds and audits a more complete Turing-frontier dataset v2 covering supported bounded control, near-supported function/array/recursion frontiers, unsupported unbounded execution, traps, review cases, and natural-language variants. It does not claim Turing completeness, solved program synthesis, or production readiness.
## v0.9.18 Development Direction

v0.9.18 introduces ForgeFrontier for experimental function/array frontier probing and IronJudge for larger real-MSVC compiler validation. IronJudge scales validation from 5k to 20k and optionally 50k real compiler invocations. ForgeFrontier evaluates pure functions without recursion, fixed-size arrays without pointers, function+bounded-control, array+bounded-loop, and limited function-array combinations while keeping recursion, pointers, IO, English, and mixed-language boundaries isolated. This version does not claim Turing completeness or production support.
## v0.9.18.1 Development Direction

v0.9.18.1 turns IronJudge into a resumable, checkpointed compiler-validation pipeline after v0.9.18 produced positive function/array frontier signals but only partial 5K/20K/50K validation. The version resumes real MSVC cl.exe validation, tracks invocation accounting, prevents cached results from being counted as new validation, and attempts to complete 5K, 20K, and optionally 50K compiler checks. It does not introduce new capabilities or claim production function/array support.

## v0.9.18.2 Development Direction

v0.9.18.2 reconciles IronJudge accounting after v0.9.18.1 produced 27,800 accounted real-MSVC compiler invocations but reported inconsistent level completion fields. The version clarifies cumulative vs independent level semantics, fixes claim/readiness consistency, and resumes main_20k validation if needed. It does not add new capabilities or claim production function/array support.

## v0.9.19 Development Direction

v0.9.19 performs a RedQueen Autopsy and Causal Forge analysis after v0.9.17 showed that RedQueen Curriculum and HydraBudget improved bounded-control performance. This version does not add new capabilities. Instead, it attributes RedQueen gains by data-need spec and adversarial pattern, checks template-overfit and pseudo-diversity risks, evaluates contrastive pair coverage, and introduces Regression Sentinel checks to monitor capability balance without using a traditional replay-buffer framing. It prepares a RedQueen v2 bandit-style causal curriculum scheduler.

## v0.9.20 Development Direction

v0.9.20 upgrades RedQueen into a v2 causal bandit curriculum scheduler and introduces Contrastive Forge for minimal semantic-difference training pairs. It also adds an Architecture Charter stating that JianMu capability boundaries are data-contract-defined rather than runtime-hardcoded. Regression Dashboard and Capability Balance Report are offline evaluations, not replay buffers or training-time gates. This version does not claim Turing completeness or production function/array support.

## v0.9.20.1 Development Direction

v0.9.20.1 scales RedQueen v2 with a larger six-hour loop and expands Contrastive Forge from preview audit to larger materialized contrastive auditing. It checks whether the v0.9.20 top1 >= 0.90 result can be reproduced or improved, while preserving the Architecture Charter: capability boundaries remain data-contract-defined rather than runtime-hardcoded. This version does not add new production capabilities or change the default profile.

## v0.9.21 Development Direction

v0.9.21 introduces RedQueen MirrorForge, a code/AST/IR-to-MirrorToken teacher layer. MirrorToken is a JianMu-readable semantic training token format, not natural language and not a raw target_ir dump. The version reuses existing dataset, audit, compiler-validation, RedQueen, Contrastive Forge, and Architecture Charter logic to test whether code-derived semantic tokens can become a lower-level teacher path for future NL-to-token alignment. It does not add production capabilities or change the default profile.

## v0.9.21.1 Development Direction

v0.9.21.1 probes MirrorForge abstraction robustness after v0.9.21 showed that code/AST/IR-derived MirrorToken is a strong JianMu-readable teacher layer. This version compares lossless, semantic, compressed, minimal, and noisy MirrorToken variants, performs field ablations and perturbation tests, audits IR-similarity/leakage risk, and assesses readiness for a future NL-to-MirrorToken adapter. It does not implement a natural language layer or change production capability boundaries.

## v0.9.22 Development Direction

v0.9.22 introduces RedQueen CodeCartographer, a single-module code-to-Project-StandardToken teacher path. It parses supported-subset code modules into classification descriptors and structured logic descriptors, then emits JianMu-readable StandardToken training samples. RedQueen can issue targeted required-feature assignments so future datasets include the structures most needed by current failure modes. This version reuses existing MirrorForge, RedQueen, compiler-validation, dataset-audit, and Architecture Charter logic. It does not implement arbitrary project parsing, natural language understanding, production support, or real promotion.

## v0.9.23 Development Direction

v0.9.23 introduces a RedQueen Symbiote freeze-thaw co-training probe. It treats Mirror/CodeCartographer as a code-structure translator, the main trunk as a StandardToken solver, the compiler as the final verifier, and RedQueen as a curriculum scheduler. The probe alternates frozen-trunk mirror training and frozen-mirror trunk training while checking for comfort-zone collapse and heldout module generalization. This is symbiotic verified co-training, not GAN-style adversarial training, and it does not change production capability boundaries.

## v0.9.24 Development Direction

v0.9.24 performs a V1.0 freeze-candidate audit after the RedQueen Symbiote freeze-thaw co-training result. It does not add new capabilities. Instead, it aggregates evidence from v0.9.17 through v0.9.23, checks claim discipline, data-contract cleanliness, compiler-validation evidence, Architecture Charter compliance, module roles, and remaining risks. The output is a human-review-ready V1.0 freeze-candidate bundle, not a V1.0 release.

## v0.9.25 Development Direction

v0.9.25 performs a longhaul Symbiote stability test and a machine-assisted human-review fixpack for the v1.0 freeze candidate bundle. It checks rolling-window stability, plateau behavior, comfort-zone collapse risk, heldout generalization, compiler validation, large-file hygiene, and release-candidate wording. This version does not add new capabilities, does not enable real promotion, and does not release v1.0.

## v0.9.26 Development Direction

v0.9.26 opens the Turing-substrate frontier by adding experimental unbounded while, recursion, and state-growth evidence, together with counter-machine and WHILE-language constructive mappings. Runtime validation remains watchdog-limited, and finite tests are not claimed as a formal proof of Turing completeness. This version also enforces a wall-clock longhaul rule: endurance runs below 6 hours must be marked partial.

## v0.9.28 Development Direction

v0.9.28 reviews the function/array frontier and Turing frontier evidence after the v0.9.27.1 clean rerun. It organizes counter-machine and WHILE-language constructive proof artifacts, checks claim wording, and prepares a v1.0 RC1 readiness bundle. Constructive expressivity evidence and finite compiler validation are not treated as a formal proof of Turing completeness.

## v0.9.28.1 Development Direction

v0.9.28.1 performs a full-compile 50K continuation by adding 30K new full compile/link/run validations on top of the previous clean 20K evidence from v0.9.27.1. It is an evidence-thickness pass only: no new capabilities, no production promotion, no default profile change, and no v1.0 release.

## V1.0 Source Review Candidate

This branch is a V1.0 source review candidate. It is not a production release, not a formal proof of Turing completeness, and not an official V1.0 release tag. Human review is still required before any official V1.0 release or tag. The current review evidence includes 50K accounted clean full-compile validation, while preprint or paper materials may still be pending.

## Current Status

JianMu V1.0 Source Review Candidate is a public review candidate, not an official release and not production ready. It has 50K clean full-compile evidence, while human review is still required before any official release or tag.

## Development Baseline

Post-V1.0 development starts from the source review candidate and the baseline guide in [POST_V1_0_DEVELOPMENT_BASELINE.md](docs/development/POST_V1_0_DEVELOPMENT_BASELINE.md).

## v1.0.2 Development Direction

v1.0.2 hardens the post-V1.0 substrate before the natural-language layer by testing controlled small-project parsing through CodeCartographer / MirrorForge into Project StandardToken, MirrorToken, and TuringToken. It keeps natural-language work on a side alpha path, does not claim arbitrary project parsing, and does not enable production support.

## v1.0.3 Development Direction

v1.0.3 explores ForgeCorpus Classic C Algorithm Substrate. After v1.0.2 validated controlled small-project parsing, this version introduces deterministic classic C algorithm families and optional license-audited manual drop-in corpus, then tests whether Mirror / ProjectCartographer can decompose single-file composite algorithms into Project StandardToken, MirrorToken, and TuringToken. This is not arbitrary project parsing, not production support, and not a formal proof of Turing completeness.

## Archive

Historical v0.9.x evidence is preserved through archive indexes:

- [V0_9_EXPERIMENT_ARCHIVE_INDEX.md](docs/archive/V0_9_EXPERIMENT_ARCHIVE_INDEX.md)
- [V0_9_RECORDS_EVIDENCE_MAP.md](docs/archive/V0_9_RECORDS_EVIDENCE_MAP.md)
- [V1_0_EVIDENCE_PRESERVATION.md](docs/archive/V1_0_EVIDENCE_PRESERVATION.md)
## v1.0.4.1 Development Direction

v1.0.4.1 explores RedQueen Symbol Binding Longhaul. After v1.0.4 introduced controlled C systems frontier, this version focuses on identifier recognition and semantic binding across variables, functions, parameters, pointers, malloc buffers, FILE handles, struct fields, and multi-file declarations. It uses AST/symbol-table guided rename plus guarded regex-like perturbation, and requires a minimum 6-hour longhaul run with real compiler accounting.
