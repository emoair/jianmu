# v0.9.22 RedQueen CodeCartographer Module-to-StandardToken Teacher

## Why v0.9.22 Exists

MirrorForge showed that code/AST/IR-derived tokens can be a strong JianMu-readable teacher layer. v0.9.22 takes the next lower-level engineering step: ingest a single supported-subset code module, describe it, and emit Project StandardToken samples for future code-derived training data.

Natural-language alignment stays later. This version prepares the code-module ingestion path first.

## What CodeCartographer Is

CodeCartographer is a single-module code ingestion adapter. It is not an arbitrary C/C++ production parser. It parses a supported subset into module descriptors, function descriptors, feature classification descriptors, structured logic descriptors, Project StandardToken, reconstructed IR/candidate views, and compiler validation.

## What Project StandardToken Is

Project StandardToken combines classification descriptors with structured code-logic descriptors. It is JianMu-readable project training token data. It is not natural language, not raw `target_ir`, and not a C source dump.

## RedQueen Targeted Assignment

RedQueen emits required-feature and difficulty profiles for future module generation, such as loop-bound contrast, condition-operator contrast, update-order contrast, output-variable contrast, function-frontier examples, and array-frontier examples. RedQueen adjusts data mix and curriculum only; it does not change capability boundaries.

## Reuse-First Rule

This version reuses MirrorForge token/audit/roundtrip patterns, RedQueen scheduling concepts, existing compiler-validation utilities, dataset records style, and the Architecture Charter guard. It adds only the adapter and diagnostic records needed for module-to-token probing.

## Non-Claims

This version does not implement arbitrary project parsing, a natural-language layer, production support, real promotion, Turing completeness, or solved program synthesis.
