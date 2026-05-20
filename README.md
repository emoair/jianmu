# JianMu MVP

JianMu v0.5 is a Chinese-first hierarchical semantic routing runtime for
compiler-validated deterministic program rewriting.

Author: Huang Linquan (空气)

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
