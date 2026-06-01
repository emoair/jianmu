# RedQueen MirrorForge Code-to-Token Teacher

## Why v0.9.21 Exists

v0.9.20.1 pushed RedQueen v2 + Contrastive + HydraBudget to top1 0.9120. The next step is not to jump directly into a natural-language layer. v0.9.21 builds a lower-level teacher path from code/AST/IR into JianMu MirrorToken, preparing a later NL -> MirrorToken -> IR bridge.

## What MirrorToken Is

MirrorToken is a JianMu-readable semantic training token format. It is deterministic from AST/IR, not natural language, not a raw target_ir dump, not C source, and not expected_output leakage. target_ir remains a label and validation target, not a free-inference input.

## Why This Helps

MirrorToken is lower-level and less ambiguous than Chinese task text. It can turn code-derived structure into auditable training fuel, while future natural-language adapters can align to the same token grammar.

## Reuse-First Rule

This version reuses existing dataset schema, audit style, compiler validation, RedQueen curriculum, Contrastive Forge logic, IronJudge/MSVC utilities, Architecture Charter guard, and records/readiness conventions. It adds adapter and teacher-layer diagnostics only.

## Non-Claims

v0.9.21 does not claim Turing completeness, solved program synthesis, production readiness, default profile change, real promotion, production function/array/recursion support, or a completed natural-language layer.
