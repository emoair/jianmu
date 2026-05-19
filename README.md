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
