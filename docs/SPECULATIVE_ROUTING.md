# JianMu Speculative Routing (v0.4)

## Why v0.3 Was Not Yet JianMu

v0.3 proved that `ProgramIR + Expert + CEmitter + C compiler Sandbox` works as an execution backend.
But its `IntentRouter` was a **final decision-maker**: one input → one intent → one expert chain → one program.

That is not JianMu. In JianMu, rules can only **propose candidates**. The compiler and runtime are the **judges**.

---

## What v0.4 Adds

```
user_input
  → SpeculativeRouter.generate_candidates()   # produces ≥3 RouteCandidate
  → RouteMemory adjusts prior_score           # history-informed ranking
  → sort by prior_score, execute top_k
  → CandidateExecutor runs each candidate:
      ProgramIR → CEmitter → gcc / clang / MSVC cl → run → ScoreReport
  → select winner by correctness_score == 1.0
  → RouteMemory.record(winner=success, losers=failure)
  → TraceCache.put() only for winner
  → return RuntimeResult with full audit trail
```

---

## Core Concepts

### RouteCandidate
A proposed execution path. Contains:
- `route_id` — unique name (e.g. `"append_literal_to_existing_sum"`)
- `intent` — structured dict passed to CandidateExecutor
- `expert_plan` — list of expert class names to apply
- `prior_score` — initial ranking score (boosted by RouteMemory history)
- `requires_previous_ir` — whether this route needs an existing IR
- `rationale` — human-readable explanation

### CandidateExecutor
Executes one RouteCandidate end-to-end:
`intent → ProgramIR → CEmitter → Sandbox → Scorer → CandidateExecutionResult`

Every candidate is truly compiled and run. No shortcuts.

### RouteMemory (QTable)
Stores per-situation, per-route experience:
- `success_count`, `failure_count`, `avg_score`
- Key = coarse semantic situation (operation class + has_previous_ir)
- Used to boost `prior_score` of historically successful routes

**RouteMemory ≠ TraceCache**

| | TraceCache | RouteMemory |
|---|---|---|
| What it stores | Final code result for a specific intent | Route-level success/failure experience |
| Key | sha256(intent + prev_ir) | semantic situation class |
| Purpose | Avoid re-generating known-good code | Prioritize historically successful routes |
| Written when | correctness_score == 1.0 | After every execution (win or lose) |

### Execution Feedback as Judge
The winner is selected by `correctness_score == 1.0` (compile + run + output match + consistency).
`prior_score` only determines execution order, never the winner.

---

## Current Limitations

- `SpeculativeRouter` still uses rule-based candidate generation — not a learned router
- Only 3 candidate routes are defined for the sum domain
- `_situation_key` uses coarse operation-class matching — not true semantic similarity
- No speculative execution across different program domains
- RouteMemory does not yet implement decay or forgetting
