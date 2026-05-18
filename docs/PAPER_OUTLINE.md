# Paper Outline

## Title Candidate

**JianMu: Compiler-Validated Deterministic Expert Routing for Compositional Program Rewriting**

---

## Abstract (Draft)

Large language models for code generation rely on continuous-space pattern matching, which introduces hallucination, non-determinism, and structural inconsistency. We present JianMu, a deterministic structural program rewriting runtime that routes natural language intent through a structured intermediate representation, applies composable atomic experts, and validates correctness inline via compiler feedback. On a minimal program domain (integer summation in C), we demonstrate that a system seeded with only a two-operand addition structure can compositionally generalize to three- and four-operand summation through expert composition, with all outputs verified by GCC compilation and execution. We introduce a trace cache that records successful structural paths for deterministic replay. We make no claims about general code intelligence or scalability beyond this domain; our contribution is a proof-of-concept that compiler-validated compositional structural generalization is achievable in a constrained, verifiable setting.

---

## 1. Introduction

- The reliability gap in LLM-based code generation
- Motivation for deterministic, compiler-grounded approaches
- Overview of JianMu's pipeline and research scope
- Summary of contributions

## 2. Motivation

- Structural inconsistency and hallucination in LLM code generation
- The case for discrete, compositional program representations
- Why compiler feedback is a natural correctness oracle
- Scope limitation: why a minimal domain is the right starting point

## 3. System Design

- End-to-end pipeline: Intent → IR → Expert → CEmitter → Sandbox → Scoring → TraceCache
- Design principles: determinism, composability, verifiability
- Module responsibilities and interaction protocol

## 4. ProgramIR and Expert Composition

- ProgramIR: a typed, structured intermediate representation for C programs
- Expert definition: atomic structural transformation with pre/post conditions
- Composition mechanism: how two-operand addition extends to N-operand via expert application
- Anti-template guarantee: experts operate on IR, not on source code strings

## 5. Compiler Feedback and Deterministic Replay

- Sandbox design: GCC compilation + execution in isolation
- Inline validation: compiler error as a first-class signal, not post-processing
- Determinism guarantee: same IR always produces byte-identical C source
- Failure handling: compile error propagation back to the routing layer

## 6. Trace Cache

- Structure: Intent → IR → source hash → expected output
- Cache lookup protocol and hit conditions
- Role in deterministic replay and experiment reproducibility
- Scope: cache is a record of verified paths, not a generalization mechanism

## 7. Experiments

- E1: Two-operand summation baseline
- E2: Three-operand compositional generalization
- E3: Four-operand compositional generalization
- E4: Natural language variant normalization
- E5: Deterministic replay verification
- E6: Trace cache hit on repeated isomorphic task
- E7: Template leak absence verification
- Results table against evaluation metrics defined in EVALUATION.md

## 8. Limitations

- Domain is intentionally minimal; results do not generalize beyond integer summation
- Expert set is hand-designed; no learning or search over expert space
- IntentRouter uses rule-based normalization; no semantic parsing
- No evaluation on real-world software engineering tasks
- Scalability to larger program domains is an open question

## 9. Future Work

- Extending ProgramIR to cover broader C constructs (conditionals, loops)
- Learned expert selection over a larger expert library
- Integration with symbolic execution for richer correctness signals
- Comparison with neuro-symbolic program synthesis approaches
- Exploration of whether the trace cache can seed generalization to unseen structures

---

## Contributions (Scoped)

1. A compiler-validated deterministic structural rewriting runtime for a minimal program domain
2. A proof-of-concept of compositional structural generalization from two-operand to N-operand summation
3. Inline execution feedback as a runtime correctness signal, not post-processing
4. A trace cache mechanism for deterministic path recording and replay
5. A discussion of the relationship between this approach and LLM code generation / neuro-symbolic program synthesis
