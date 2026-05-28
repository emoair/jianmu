# v0.9.12.3 Layerwise Compiler Failure Taxonomy + Clean Rerun

## Why v0.9.12.3 Exists

v0.9.12.2 showed a strong diagnostic signal for the layerwise sparse 1B freeze-prune profile, but its MSVC compiler validation was not clean. Before any profile-promotion probe, JianMu must classify those compiler failures and verify whether a clean MSVC environment restores validation.

## What Is Being Diagnosed

This version diagnoses environment, 360/Defender, stale process, Windows file-lock, MSVC cl/link lifecycle, cleanup race, candidate C source, wrong stdout, and freeze-prune transfer mapping issues. It does not assume the failure is environmental: candidate/program and freeze-prune semantic failures are separate taxonomy categories.

## Original vs Clean Rerun

The original v0.9.12.2 records are preserved as read-only inputs. v0.9.12.3 writes taxonomy, failure replay, clean rerun, reduced-worker fallback, readiness, and conclusion records separately under `records/v0_9_12_3/`.

## Non-Claims

This version does not promote any profile. It does not claim Turing completeness, solved program synthesis, production readiness, or emergence proven.
