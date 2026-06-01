# v0.9.23 RedQueen Symbiote Freeze-Thaw Co-Training

## Why v0.9.23 Exists

v0.9.22 showed that a single code module can be converted into Project StandardToken teacher data. v0.9.23 tests whether Mirror/CodeCartographer and the main trunk can be alternately frozen and improved in a shadow diagnostic loop.

This is symbiotic verified co-training, not GAN-style adversarial training.

## Symbiotic Teacher Loop

Mirror/CodeCartographer translates code structure into Project StandardToken. The trunk digests StandardToken and produces candidate behavior. The compiler is the final verifier. RedQueen schedules curriculum and required features. The truth anchors remain parser/AST structure, dataset schema, token audits, roundtrip checks, real compiler stdout, and heldout module generalization.

## Freeze-Thaw Protocol

The probe records frozen trunk snapshots, frozen mirror snapshots, thawed components, training targets, update scope, allowed state changes, disallowed state changes, and restore checks. The snapshots are represented by persisted profiles, router roots, curriculum policies, schema hashes, and dataset manifests; no neural framework is introduced.

## Anti-Collapse Checks

The probe audits comfort-zone collapse, trunk-friendly token bias, semantic diversity, difficulty distribution, heldout module generalization, structural truth mismatch, and compiler-pass-but-structure-wrong cases.

## Non-Claims

This version does not enable real promotion, does not change the default profile, does not add production support, does not implement arbitrary project parsing, does not implement a natural-language layer, and does not claim Turing completeness.
