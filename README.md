# JianMu MVP

A **Deterministic Structural Program Rewriting Runtime** for a minimal program domain.

JianMu routes natural language intent through a structured IR, applies composable atomic experts,
and validates correctness inline via compiler feedback.

## Requirements

- Python 3.8+
- `gcc` or `clang` (for compilation tests)
- `pytest` (`pip install pytest`)

## Run the demo

```bash
cd jianmu-mvp
python examples/demo_sum.py
```

## Run tests

```bash
cd jianmu-mvp
python -m pytest tests/ -v
```

Compilation-dependent tests are automatically skipped if `gcc`/`clang` is not found.

---

## What this project DOES prove

- In a minimal C integer summation domain, structural expert composition can extend a
  two-operand addition to three- and four-operand addition **without hardcoded templates**.
- Compiler feedback (GCC/Clang) serves as a deterministic inline correctness signal.
- A trace cache can record and deterministically replay successful structural paths.
- A limited set of natural language variants (Chinese and English) can be normalized to
  structured intent via rule-based keyword matching.
- `CEmitter` produces byte-identical C source for the same `ProgramIR`.
- Limited value generalization is supported: e.g. `"1加2加3"` → compiles and outputs `6`.

## What this project does NOT prove

- **General code intelligence** — the system only handles C integer summation.
- **Scalability** beyond integer summation or variable counts beyond single digits.
- **A replacement for LLMs** — no semantic understanding, no cross-domain generalization.
- **A replacement for compilers** — GCC/Clang is used as the correctness oracle.
- **True natural language understanding** — `IntentRouter` is keyword/regex matching,
  not NLU. It fails on unseen phrasings.
- **Complex arithmetic** — no support for negative numbers, zero, multi-digit edge cases,
  multiplication, subtraction, or parenthesized expressions.
- **Real-world software engineering effectiveness**.
- **Hardware architecture feasibility** at any scale.
- **AGI or general program synthesis**.

---

## Known limitations (v0.3)

1. `IntentRouter` covers a limited set of Chinese and English phrases; arbitrary natural
   language input will fail.
2. `CEmitter` is string concatenation, not AST rewrite — no syntactic validation of IR.
3. No support for negative numbers, zero, or systematic benchmark across input variants.
4. No support for multiplication, subtraction, or bracket precedence.

See `CRITIQUE.md` for a full red-team audit and `ROADMAP_V03.md` for next steps.
