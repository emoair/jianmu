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
