# JianMu MVP

A **Deterministic Structural Program Rewriting Runtime** with **Speculative Execution Routing**.

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

- A rule router can be demoted from **final decision-maker** to **candidate generator**
- Multiple expert chains can be executed speculatively and ranked by real compiler/runtime feedback
- `RouteMemory` can record route-level success/failure experience and influence future `prior_score`
- `TraceCache` (result cache) and `RouteMemory` (path experience) serve distinct roles
- The winner is always selected by `correctness_score == 1.0`, never by prior alone
- Chinese-first hierarchical semantic neurons can expose `SemanticFeatures` and `neuron_results`
- `expected_output_provenance` prevents candidates with untrusted expected outputs from self-certifying

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

## Known limitations (v0.5)

1. `SpeculativeRouter` generates candidates by rules, not by learned priors
2. `_situation_key` uses coarse operation-class hashing — not true semantic similarity
3. Only 3 candidate routes exist for the sum domain
4. No speculative execution across different program domains
5. `CEmitter` is still string concatenation, not AST rewrite
6. Non-addition expressions such as `1-2`, `1*2`, and `1/2` are intentionally unsupported in v0.5
7. Limited negative literal cases are supported, but systematic arithmetic parsing is not

See `CRITIQUE.md`, `docs/SPECULATIVE_ROUTING.md`, and `ROADMAP_V03.md` for details.
