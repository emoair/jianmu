# Turing Frontier Dataset and Candidate-Space Scale Probe

v0.9.9 exists because v0.9.8.1 identified candidate miss as the dominant bounded-substrate plateau cause. Beam-size and ranking bottlenecks were not dominant, so this version prepares broader Turing-frontier data and probes candidate-space coverage budgets before any scorer/router change.

"Turing frontier" means a curriculum spectrum of language structures on the path toward Turing-complete programming: variables, assignment, conditionals, bounded loops, functions, arrays, recursion, unbounded loops, memory-like patterns, IO/system-call traps, ambiguity cases, and review candidates. It does not mean JianMu is Turing complete. The current supported subset remains separated from future-domain and unsupported structures.

Newly included frontier structures are functions, arrays, recursion, unbounded loops, pointer-like and memory-like patterns, IO/system-call traps, semantic ambiguity cases, and label-review candidates. Unbounded execution, unrestricted recursion, dynamic memory, file IO, system calls, user input, and production program synthesis remain unsupported.

The candidate-space scale probe sweeps beam size, candidate budget, control-template budget, root/sub-root expansion budget, and memory-slot budget in phased diagnostics rather than a Cartesian search. Sweep outputs are diagnostic only and do not replace mainline training results.

Non-claims: no Turing completeness, no solved program synthesis, no safe real promotion, and no production readiness.
