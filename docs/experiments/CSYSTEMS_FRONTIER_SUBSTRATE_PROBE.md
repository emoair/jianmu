# v1.0.4 CSystems Frontier Substrate Probe

## 1. Why C Systems Frontier

v1.0.3.1 validated controlled classic C algorithm variants. Real C programs often also involve pointer basics, malloc/free lifecycle, sandboxed file IO, multi-file build/link, and simple struct patterns. v1.0.4 tests whether these controlled systems features can enter the ProjectToken / MirrorToken / TuringToken substrate without changing JianMu's core architecture.

## 2. Scope

This version is limited to controlled C systems frontier samples: pointer basics, pointer parameters, array pointer traversal, malloc/free lifecycle, sandboxed file IO, multi-file compile/link, and simple structs.

It is not arbitrary project parsing, arbitrary filesystem IO, complex pointer support, memory safety completion, or production support.

## 3. Full Scale Rule

Full scale must be attempted and completed before the recommended claim level can be positive. If full scale is not completed, readiness must include `full_scale_not_completed` and cannot claim positive completion.

## 4. Validation

`cl.exe /Zs` is a syntax frontend filter only. Correctness evidence comes from full compile, link, run, and stdout validation. File IO samples run inside temporary sandbox working directories, and multi-file samples use real multi-file compile/link validation.

## 5. Non-Claims

- no arbitrary project parsing completed
- no memory safety solved
- no file IO production support
- no multi-file project production support
- no formal Turing completeness proven
- no solved program synthesis
- no production readiness
- no natural language layer completed
- no emergence proven
