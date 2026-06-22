# RedQueen Multi-round Stability and MSVC Guard

## 1. What this version does

v1.0.8.6 adds an MSVC compiler environment preflight guard and runs an 8-hour RedQueen multi-round stability validation.

It verifies that RedQueen remains stable across repeated weak-signal, recovery, all-stable, and perturbation cycles while keeping the real compile lane clean.

## 2. What this version does not do

This version does not claim:

- production function support completed
- production array support completed
- production recursion support completed
- production readiness
- official release
- formal Turing completeness proven
- solved program synthesis
- natural language layer completed
- arbitrary project parsing completed
- RedQueen autonomous governance completed
- model training completed

## 3. MSVC environment rule

If `cl.exe` or `link.exe` is unavailable, the runner must fail fast before validation starts.

It must clearly tell the user to run under:

- x64 Native Tools Command Prompt for VS
- or a `vcvars64.bat` initialized shell

Ordinary PowerShell without MSVC initialization must not run until the middle of validation and then fail.

## 4. Stability honesty rule

Synthetic weak signals remain shadow governance metrics only.

They must not affect real compiler correctness.

They must not be claimed as real compiler failure or real compiler recovery.
