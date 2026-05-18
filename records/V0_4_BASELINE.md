# JianMu MVP v0.4 Baseline

## Status

v0.4 clean baseline. Speculative execution routing added on top of v0.3 scaffold.

## New in v0.4

- `SpeculativeRouter`: generates ≥3 `RouteCandidate` per input
- `CandidateExecutor`: executes each candidate end-to-end (ProgramIR → gcc → run)
- `RouteMemory`: records per-route success/failure experience, boosts prior_score
- `Runtime.run(..., speculative=True)`: full speculative pipeline
- `ReplaceOperandExpert`: new atomic expert
- `RuntimeResult` extended with full audit trail fields
- 10 new speculative routing tests (39 total)

## Core Capabilities (v0.3 preserved)

- Deterministic IntentRouter
- ProgramIR-based structural generation
- Atomic expert composition
- CEmitter (byte-identical)
- GCC/Clang sandbox validation
- TraceCache (result cache, write only on correctness_score==1.0)
- Scoring with correctness/runtime split
- Limited Chinese/English intent normalization
- Numeric generalization (1+2+3=6)

## What v0.4 Proves

- A rule router can be demoted to candidate generator; execution feedback selects the winner
- Multiple expert chains can be speculatively executed and ranked by real compiler output
- RouteMemory and TraceCache serve distinct roles and can coexist
- The runtime shape (multi-candidate → execute → feedback → memory) is correct for JianMu

## What v0.4 Does NOT Prove

- Learned routing (SpeculativeRouter is still rule-based)
- True semantic similarity in RouteMemory situation keys
- General code intelligence
- AGI, replacement of LLMs or compilers
- BPU hardware co-design
- Scalability beyond C integer summation

## Test Count

- v0.3: 29 tests
- v0.4: 39 tests (+10 speculative routing tests)

## Next Steps (v0.5)

- Learned route prior (replace rule-based prior with statistical model)
- Larger candidate space (more expert combinations)
- Finer-grained situation_key in RouteMemory
- Support for subtraction, multiplication, negative numbers
- Expression tree ProgramIR (replace flat SumExpression)
- Benchmark table
