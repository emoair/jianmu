# JianMu MVP

A **Deterministic Structural Program Rewriting Runtime** with **Speculative Execution Routing**.

---

## v0.3 → v0.4

**JianMu v0.3** proved that `ProgramIR + Expert + CEmitter + GCC Sandbox` works as an execution scaffold.

**JianMu v0.4** adds speculative routing: a single input no longer maps directly to one path.
Instead, multiple `RouteCandidate` are generated, each compiled and executed, and the winner
is selected by execution feedback — not by the rule router.

```
v0.3:  input → single intent → single expert chain → compile/run
v0.4:  input → multiple RouteCandidate → parallel execution → feedback selects winner
                                                             → RouteMemory records experience
```

---

## Requirements

- Python 3.8+
- `gcc` or `clang`
- `pytest` (`pip install pytest`)

## Run demo

```bash
python examples/demo_sum.py
```

## Run tests

```bash
python -m pytest tests/ -v
```

---

## What v0.4 DOES prove

- A rule router can be demoted from **final decision-maker** to **candidate generator**
- Multiple expert chains can be executed speculatively and ranked by real compiler/runtime feedback
- `RouteMemory` can record route-level success/failure experience and influence future `prior_score`
- `TraceCache` (result cache) and `RouteMemory` (path experience) serve distinct roles
- The winner is always selected by `correctness_score == 1.0`, never by prior alone

## What v0.4 does NOT prove

- **True natural language understanding** — `SpeculativeRouter` is still rule-based candidate generation
- **Learned routing** — no statistical or neural route selection
- **General code intelligence** — domain is still C integer summation only
- **Scalability** beyond this minimal domain
- **A replacement for LLMs or compilers**
- **AGI or general program synthesis**
- **BPU hardware co-design**

---

## Known limitations (v0.4)

1. `SpeculativeRouter` generates candidates by rules, not by learned priors
2. `_situation_key` uses coarse operation-class hashing — not true semantic similarity
3. Only 3 candidate routes exist for the sum domain
4. No speculative execution across different program domains
5. `CEmitter` is still string concatenation, not AST rewrite

See `CRITIQUE.md`, `docs/SPECULATIVE_ROUTING.md`, and `ROADMAP_V03.md` for details.
