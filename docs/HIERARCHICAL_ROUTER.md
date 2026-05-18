# JianMu v0.5 Hierarchical Semantic Router

## From v0.4 to v0.5

JianMu v0.4 used a flat speculative router. It generated several route
candidates from surface rules, then let CandidateExecutor compile and run them.
That proved the execution scaffold, but the router could confuse negation,
replacement, appending, whole-expression rewrite, and multi-operand append.

JianMu v0.5 introduces a handcrafted hierarchical semantic router: a small tree
of front-end "neurons" that produce features, votes, and confidence scores before
RouteCandidate generation.

## Language Scope

v0.5 is Chinese-first. The router accepts Chinese natural-language input and
Chinese sentences mixed with technical C tokens such as `C`, `int`, `printf`,
`main`, `return`, and variable names.

Pure English natural-language input is intentionally unsupported. This language
scope reduction lowers rule complexity, reduces ambiguity, and focuses the MVP
on high-information Chinese input while the project validates runtime and router
architecture. JianMu is not trying to prove multilingual NLU.

## Neuron Layers

- L0 Domain Neurons: ArithmeticDomainNeuron, CodeEditDomainNeuron,
  CodeGenerateDomainNeuron, NoOpDomainNeuron, UnknownDomainNeuron.
- L1 Operation Neurons: AdditionNeuron, SubtractionNeuron,
  MultiplicationNeuron, DivisionNeuron, MixedExpressionNeuron.
- L2 Edit Intent Neurons: AppendOperandNeuron, AppendMultipleOperandsNeuron,
  ReplaceOperandNeuron, RewriteExpressionNeuron, KeepExistingNeuron,
  GenerateNewNeuron.
- L3 Extraction Neurons: NumberExtractorNeuron, ChineseNumberNeuron,
  ExpressionExtractorNeuron, VariableExtractorNeuron, NegationDetectorNeuron,
  QuantityExtractorNeuron.

Each neuron is deliberately local. A regex can exist inside a neuron as a small
detector, but no regex decides the final route by itself.

## Router Contract

The router does not emit C code and does not bypass ProgramIR, CEmitter, or
Sandbox. It only aggregates SemanticFeatures and converts those features into
RouteCandidate objects with semantic_match_score.

CandidateExecutor still applies expert plans to ProgramIR. CEmitter still emits
C. Sandbox still compiles and runs the generated source. The final winner is
selected by execution feedback combined with semantic_match_score.

## Current Claims

v0.5 shows that a flat speculative router can be replaced by a tree-shaped
front-end semantic scaffold while keeping deterministic execution validation.
It improves separation between local detection, candidate generation, execution,
and scoring.

## Non-Claims

This is not a learned router. The neuron tree is handcrafted and its weights are
fixed in code. It is not a general natural-language calculator, not AGI, not a
Transformer replacement, and not a claim of general code intelligence.
It is also not an English natural-language interface in v0.5.

Future work can replace individual neurons with small models or learned/evolved
weights while keeping the RouteCandidate, ProgramIR, CEmitter, and Sandbox
interfaces intact.
