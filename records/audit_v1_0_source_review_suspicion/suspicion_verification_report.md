# JianMu V1.0 Source Review Suspicion Verification

## Executive Summary

- package_audited: true
- current_workspace_audited: true
- source_review_package_zip_not_found: false
- package_path: `dist/JianMu-V1.0-source-review-package.zip`
- extracted_package_path: `C:\Users\Air\AppData\Local\Temp\jianmu_v1_audit_pkg_c73fbe08fa3d451da4212082ed8678d2\JianMu-V1.0-source-review-package`
- overall_risk_level: high
- pytest_result: pytest_failed_collection
- pytest_command: `python -m pytest tests/ -q`
- pytest_failure_summary: collection failed in `tests/test_full_compile_50k_preflight.py` and `tests/test_full_compile_50k_postflight.py` because the active Python runtime rejects `str | Path` annotations.

Strongest confirmed issues:

- Main production `ProgramIR` and `CEmitter` remain arithmetic/sum-shaped and do not expose production function, array, or recursion constructs.
- `Runtime -> CandidateExecutor -> CEmitter` can generate or transform sum/expression programs only; legacy regex and handcrafted semantic routing remain reachable.
- `AtomicSynthesis` accepts only `canonical_arithmetic_targetir`.
- Recursion appears as frontier/contract/future/unsupported evidence, not as production recursive C generation.
- ForgeFrontier function/array compiler validation uses marker `target_ir` plus template renderer C.
- Several readiness/eval modules contain fixed metric tables or direct numeric metric literals.

Strongest refuted issues:

- Current workspace, unlike the V1.0 source-review package records subset, contains raw 50K trace and manifest files under `records/v0_9_28_1/`.

Inconclusive items:

- No item is fully inconclusive. Some findings are marked partial where package and current workspace differ.

Recommended next action:

- Treat V1.0 as review evidence plus bounded production runtime, not as production function/array/recursion synthesis. Before tag/release, separate claim-boundary repair, evidence-pack repair, and real capability implementation work.

## P0 Confirmed / Refuted / Partial / Inconclusive

### P0-1 Main IR / emitter only supports arithmetic / sum scaffold

- status: confirmed
- confidence: high
- evidence:
  - package_observation:
    - `jianmu/ir.py:5`: `class Variable`
    - `jianmu/ir.py:19`: `class SumExpression`
    - `jianmu/ir.py:31`: `class ProgramIR`
    - `jianmu/ir.py:34-38`: fields are `includes`, `variables`, `expression`, `print`, `return_code`
    - `jianmu/emitter_c.py:4`: `class CEmitter`
    - `jianmu/emitter_c.py:8-18`: emits includes, one `int main(void)`, variable declarations, `printf`, and `return`
  - current_workspace_observation:
    - Same source shape observed in `jianmu/ir.py` and `jianmu/emitter_c.py`.
- impact:
  - affected claims: production runtime supports functions; production runtime supports arrays; production runtime supports recursion.
- what this does NOT mean:
  - It does not invalidate all frontier or review evidence elsewhere in the repository.
- recommended fix:
  - Real capability fix: add production IR nodes and emitter branches for function definitions/calls, arrays, returns, blocks, and recursion, with compiler traces.
- priority:
  - P0

### P0-2 Runtime to CandidateExecutor to CEmitter production path

- status: confirmed
- confidence: high
- evidence:
  - package_observation:
    - `jianmu/runtime.py:47-57`: runtime wires `IntentRouter`, `CEmitter`, `Sandbox`, `SpeculativeRouter`, `HierarchicalSemanticRouter`, `CandidateExecutor`, and `RouteMemory`.
    - `jianmu/runtime.py:60-64`: `run` selects deterministic or speculative path.
    - `jianmu/runtime.py:112-130`: deterministic path handles `generate_sum_program` and `expand_sum_program`.
    - `jianmu/runtime.py:142-143`: emits C through `CEmitter.emit` and runs sandbox.
    - `jianmu/runtime.py:182-199`: speculative path generates candidates and executes them through `CandidateExecutor.execute`.
    - `jianmu/candidate_executor.py:37`: action `expand_sum_program`.
    - `jianmu/candidate_executor.py:48`: action `generate_sum_program`.
    - `jianmu/candidate_executor.py:58`: action `replace_last_operand`.
    - `jianmu/candidate_executor.py:76`: action `rewrite_expression`.
    - `jianmu/candidate_executor.py:85`: action `unsupported_input`.
    - `jianmu/intent_router.py:1`: imports `re`.
    - `jianmu/intent_router.py:40`: uses `re.search`.
    - `jianmu/intent_router.py:165-166`: expand detection is pattern based.
  - current_workspace_observation:
    - Same runtime and candidate action structure observed.
- impact:
  - affected claims: production runtime supports functions, arrays, recursion; legacy regex/router removed from runtime path.
- what this does NOT mean:
  - It does not mean speculative routing is absent; it means the reachable executor actions still map to sum/expression scaffolds.
- recommended fix:
  - Real capability fix: add executor actions and emitter-backed IR structures for non-arithmetic production programs; isolate or remove legacy regex path if claims require it.
- priority:
  - P0

### P0-3 AtomicSynthesis target_builder_policy only accepts canonical_arithmetic_targetir

- status: confirmed
- confidence: high
- evidence:
  - package_observation:
    - `jianmu/self_learning/darwinforge/atomic_synthesis.py:19`: rejects policies not equal to `canonical_arithmetic_targetir`.
    - `jianmu/self_learning/darwinforge/atomic_synthesis.py:20`: returns `unsupported_target_builder`.
    - `jianmu/self_learning/darwinforge/atomic_synthesis.py:22-23`: builds arithmetic target then emits C.
    - `jianmu/self_learning/darwinforge/atomic_synthesis.py:29`: `build_arithmetic_target`.
    - `jianmu/self_learning/darwinforge/atomic_synthesis.py:52`: `emit_c_program`.
    - `jianmu/self_learning/darwinforge/branch_chain.py:16`: lists `canonical_program_targetir`, but AtomicSynthesis does not accept it.
  - current_workspace_observation:
    - Same AtomicSynthesis policy gate observed.
- impact:
  - affected claims: AtomicSynthesis can synthesize non-arithmetic programs; function/array/recursion production synthesis.
- what this does NOT mean:
  - It does not prove no other experimental module renders function/array C templates.
- recommended fix:
  - Real capability fix: add explicit target builders and synthesis/evidence paths for function, array, and recursion policies.
- priority:
  - P0

### P0-4 Turing frontier recursion C generation

- status: confirmed
- confidence: high
- evidence:
  - package_observation:
    - `jianmu/self_learning/darwinforge/turing_frontier_schema.py:107`: recursion appears as `recursive_function_call_graph`.
    - `jianmu/self_learning/darwinforge/turing_frontier_schema.py:264`: supported samples use marker `target_ir` with tokens and sample id.
    - `jianmu/self_learning/darwinforge/turing_substrate_grammar.py:61-68`: recursion appears inside `unsupported_template`.
    - `jianmu/self_learning/darwinforge/turing_substrate_grammar.py:105-124`: renderer supports `VarDecl`, `Assign`, `Print`, `IfElse`, `ForBounded`, and `WhileBoundedFuel`, not function definitions or recursion.
    - `jianmu/self_learning/darwinforge/turing_proof_function_array_frontend_scaleup.py:217`: `recursion_in_current_supported_count` is 0.
    - `jianmu/self_learning/darwinforge/turing_proof_function_array_frontend_scaleup.py:338`: `recursion_production_compiled_count` is 0.
  - current_workspace_observation:
    - Same source structure observed.
- impact:
  - affected claims: recursion production support; formal Turing completeness proven; recursion frontier review-ready if stated as production C generation.
- what this does NOT mean:
  - It does not deny token/contract/frontier evidence for recursion categories.
- recommended fix:
  - Evidence pack fix for frontier claims; real capability fix for recursive function IR/emitter/compiler traces.
- priority:
  - P0

### P0-5 ForgeFrontier function/array marker IR plus template renderer

- status: confirmed
- confidence: high
- evidence:
  - package_observation:
    - `jianmu/self_learning/darwinforge/forgefrontier_compiler_validation.py:16`: `render_forgefrontier_c_source`.
    - `jianmu/self_learning/darwinforge/forgefrontier_compiler_validation.py:17-18`: reads `target_ir.stdout` and `target_ir.kind`.
    - `jianmu/self_learning/darwinforge/forgefrontier_compiler_validation.py:19-23`: hard-coded function/array C templates are selected by kind.
    - `jianmu/self_learning/darwinforge/forgefrontier_compiler_validation.py:71`: compiler validates renderer output.
    - `jianmu/self_learning/darwinforge/forgefrontier_compiler_validation.py:104`: `recursion_compiled_count` remains 0.
    - `jianmu/self_learning/darwinforge/forgefrontier_eval.py:8-16`: `GROUP_DELTAS` fixed group metrics.
  - current_workspace_observation:
    - Same ForgeFrontier compiler validation and eval structure observed.
- impact:
  - affected claims: function/array frontier review-ready; production runtime supports functions/arrays.
- what this does NOT mean:
  - It does not mean the renderer-generated C never compiles; it means the path is experimental/template validation, not production synthesis.
- recommended fix:
  - Evidence pack fix: preserve raw per-sample traces and provenance showing whether IR was generated or templated. Real capability fix: connect autonomous IR generation to production emitter.
- priority:
  - P0

### P0-6 50K full compile raw trace replayability

- status: partial
- confidence: high
- evidence:
  - package_observation:
    - `records/v0_9_28_1/full_compile_50k_accounting.json:7`: alternate clean validation source is used.
    - `records/v0_9_28_1/full_compile_50k_accounting.json:10`: names missing required files.
    - `records/v0_9_28_1/full_compile_50k_accounting.json:13-20`: accounts 30K continuation plus 20K previous evidence.
    - `records/v0_9_28_1/full_compile_50k_readiness.json:17`: summary says 50K clean completed.
    - package records search found no `*trace*`, `*.jsonl`, or `*manifest*` trace files.
  - current_workspace_observation:
    - `records/v0_9_28_1/full_compile_50k_trace_000.jsonl`: raw trace exists in current workspace.
    - `records/v0_9_28_1/full_compile_50k_trace_manifest.json`: manifest exists in current workspace.
- impact:
  - affected claims: 50K clean compiler validation; 50K replayable raw trace package.
- what this does NOT mean:
  - It does not refute the accounting summary. It says the audited package does not include enough raw trace material for independent replay.
- recommended fix:
  - Evidence pack fix: include raw trace shards, manifest, previous 20K source files, and provenance/alternate-source notes in the package.
- priority:
  - P0

### P0-7 Fixed metrics / readiness scaffold

- status: confirmed
- confidence: high
- evidence:
  - package_observation:
    - `jianmu/self_learning/darwinforge/forgefrontier_eval.py:8-16`: fixed `GROUP_DELTAS`.
    - `jianmu/self_learning/darwinforge/forgefrontier_eval.py:35-53`: direct numeric metric literals.
    - `jianmu/self_learning/darwinforge/adaptive_layerwise_eval.py:28`: metrics loaded from `BASE_METRICS`.
    - `jianmu/self_learning/darwinforge/turing_proof_function_array_frontend_scaleup.py:372-409`: direct function/array success-rate literals.
    - `jianmu/self_learning/darwinforge/turing_proof_function_array_frontend_scaleup.py:582-584`: direct bounded and token-to-IR metrics.
    - `jianmu/self_learning/darwinforge/v0_9_14_readiness.py:35-36`: integrity fields assert no fixed/summary-only detection, but no universal `metric_source` requirement was observed.
  - current_workspace_observation:
    - Same fixed/scaffold candidates observed; current workspace contains additional later records but they do not remove these source-level concerns.
- impact:
  - affected claims: readiness metrics computed from raw predictions; function/array frontier review-ready; Turing frontier review-ready.
- what this does NOT mean:
  - It does not prove every metric is fixed. Some modules compute metrics from rows or raw traces.
- recommended fix:
  - Evidence pack fix: require `metric_source` and raw-trace provenance for each published metric.
- priority:
  - P0

### P0-8 v1.1-alpha NL claim support in V1.0 package

- status: partial
- confidence: medium
- evidence:
  - package_observation:
    - `NOT_PROVEN.md:14`: lists `natural language layer completed` as not proven.
    - `V1_0_CLAIM_BOUNDARY.md:21`: lists `natural language layer completed` as not proven.
    - `README.md:576-584`: MirrorToken/StandardToken paths are future teacher paths and not production NL.
    - package records contain only `v0_9_26_1`, `v0_9_27_1`, `v0_9_28`, and `v0_9_28_1` directories.
  - current_workspace_observation:
    - Current workspace contains later v1.1/NL-adjacent source and records, but these are outside the V1.0 package evidence boundary.
- impact:
  - affected claims: natural language layer completed; v1.1-alpha NL metrics supported by V1.0 package.
- what this does NOT mean:
  - It does not deny the existence of later NL-adjacent work in the current workspace.
- recommended fix:
  - Claim boundary fix for V1.0 package; evidence pack fix if v1.1-alpha claims are separately audited.
- priority:
  - P0

## P1 Findings

### P1-1 Turing substrate is bounded-only in production renderer

- status: confirmed
- confidence: high
- evidence:
  - `jianmu/self_learning/darwinforge/turing_substrate_grammar.py:7-16`: supported stages are declarations, assignments, if/else, bounded for, bounded while with fuel, and nested bounded control.
  - `jianmu/self_learning/darwinforge/turing_substrate_grammar.py:61-80`: unbounded while, recursion, arrays, and functions are unsupported/future templates.
  - `jianmu/self_learning/darwinforge/turing_substrate_grammar.py:105-124`: renderer has no function/array/recursion statement renderer.
- impact:
  - affected claims: bounded substrate evidence; formal Turing completeness proven.
- what this does NOT mean:
  - It does not invalidate bounded substrate compiler evidence.
- recommended fix:
  - Keep bounded claims bounded, or add real unbounded/recursion/function/array renderer and compiler traces.
- priority:
  - P1

### P1-2 turing_frontier_v2 feature metadata and target_ir mismatch

- status: confirmed
- confidence: high
- evidence:
  - `jianmu/self_learning/darwinforge/turing_frontier_v2_generator.py:45`: supported samples use `_supported_print_ir`.
  - `jianmu/self_learning/darwinforge/turing_frontier_v2_generator.py:83-84`: `_supported_print_ir` is only a print-int program.
  - `jianmu/self_learning/darwinforge/turing_frontier_v2_generator.py:117-143`: feature metadata can mark variables, loops, functions, arrays, and recursion.
- impact:
  - affected claims: v2 target IR represents full feature structure.
- what this does NOT mean:
  - It does not mean metadata is useless; it means metadata is not equivalent to executable target IR structure.
- recommended fix:
  - Align feature flags with executable IR or mark them explicitly as frontier labels.
- priority:
  - P1

### P1-3 Legacy regex / handcrafted router reachable in runtime path

- status: confirmed
- confidence: high
- evidence:
  - `jianmu/runtime.py:47-57`: runtime constructs `IntentRouter`, `HierarchicalSemanticRouter`, and `RouteMemory`.
  - `jianmu/intent_router.py:1`: imports `re`.
  - `jianmu/intent_router.py:40`, `52`, `58`, `71`, `75`, `79`, `82`, `85`, `93`, `97`, `135`, `136`, `166`: regex parsing points.
  - `jianmu/runtime.py:182-199`: speculative route is reachable when enabled.
- impact:
  - affected claims: old regex/handcrafted router not in runtime path.
- what this does NOT mean:
  - It does not say these routers are always selected in every run.
- recommended fix:
  - If claims require removal, isolate legacy router behind an explicit non-production profile and add reachability tests.
- priority:
  - P1

### P1-4 String guard tests are shallow

- status: confirmed
- confidence: high
- evidence:
  - `tests/test_runtime.py:106`: no hard-coded three/four sum template test.
  - `tests/test_active_generation_pilot.py:138-147`: source-string checks for oracle and external API names.
  - `tests/test_adaptive_layerwise_readiness.py:72-85`: source-string checks for oracle, OpenAI/requests, and keyword gate.
  - `tests/test_turing_substrate_compiler_validation.py:69-82`: source-string checks for oracle/API/keyword gate.
- impact:
  - affected claims: no handcrafted leakage; no external API; no oracle dependence.
- what this does NOT mean:
  - These tests can catch obvious forbidden tokens, but they do not prove architectural absence, data-flow absence, or runtime reachability absence.
- recommended fix:
  - Add deeper architecture tests for import graph reachability, runtime call graph, metric provenance, and trace replay.
- priority:
  - P1

## Claim Impact Matrix

| Claim | Supported? | Evidence | Risk | Required Fix |
|---|---|---|---|---|
| production runtime supports functions | No | `ProgramIR`/`CEmitter`/`CandidateExecutor` only support sum-shaped programs | High | Real function IR, emitter, executor, compiler traces |
| production runtime supports arrays | No | No production array IR/emitter path observed | High | Real array IR/emitter and sandbox trace |
| production runtime supports recursion | No | Recursion is unsupported/future/frontier; production compiled count 0 | High | Recursive function IR/emitter and raw compiler trace |
| function/array frontier review-ready | Partial | ForgeFrontier validates template-rendered C | Medium | Provenance: generated IR vs template renderer, raw trace manifest |
| recursion frontier review-ready | Partial | Token/contract evidence exists; recursive C generation not established | High | Raw recursive C generation/compile traces |
| formal Turing completeness proven | No | Bounded substrate renderer and unsupported recursion/unbounded templates | High | Formal proof plus executable unbounded/recursion evidence |
| 50K clean compiler validation | Partial | Package has accounting summary; current workspace has raw trace | Medium | Include full raw evidence in reviewed package |
| 50K replayable raw trace package | No for package, yes for current workspace | Package lacks trace shards/manifests; current workspace has them | High | Add package trace shards, manifest, previous 20K evidence |
| natural language layer completed | No for V1.0 package | NOT_PROVEN and claim boundary list NL completion as not proven | High | Separate v1.1-alpha audit or claim boundary fix |
| bounded substrate evidence | Yes, bounded only | Bounded renderer supports variable/control-flow subset | Medium | Keep claim bounded; do not upgrade to Turing completeness |

## Evidence Provenance Matrix

| Metric / Evidence | Source Type | Raw Trace? | Summary Only? | Fixed Scaffold? | Path |
|---|---|---:|---:|---:|---|
| Main ProgramIR fields | computed_from_raw_trace | false | false | false | `jianmu/ir.py` |
| Production CEmitter shape | computed_from_raw_trace | false | false | false | `jianmu/emitter_c.py` |
| Runtime candidate actions | computed_from_raw_trace | false | false | false | `jianmu/candidate_executor.py` |
| AtomicSynthesis policy gate | computed_from_raw_trace | false | false | false | `jianmu/self_learning/darwinforge/atomic_synthesis.py` |
| ForgeFrontier GROUP_DELTAS | fixed_readiness_scaffold | false | false | true | `jianmu/self_learning/darwinforge/forgefrontier_eval.py` |
| ForgeFrontier compiler validation | synthetic_fixture | false | false | true | `jianmu/self_learning/darwinforge/forgefrontier_compiler_validation.py` |
| Turing proof function/array metrics | fixed_readiness_scaffold | false | false | true | `jianmu/self_learning/darwinforge/turing_proof_function_array_frontend_scaleup.py` |
| Turing substrate compiler validation | computed_from_raw_trace | true | false | false | `jianmu/self_learning/darwinforge/turing_substrate_compiler_validation.py` |
| Package 50K accounting | summary_accounting | false | true | false | `records/v0_9_28_1/full_compile_50k_accounting.json` |
| Package 50K readiness | summary_accounting | false | true | false | `records/v0_9_28_1/full_compile_50k_readiness.json` |
| Current 50K trace | computed_from_raw_trace | true | false | false | `records/v0_9_28_1/full_compile_50k_trace_000.jsonl` |
| Current 50K trace manifest | computed_from_raw_trace | true | false | false | `records/v0_9_28_1/full_compile_50k_trace_manifest.json` |
| NL completed claim boundary | loaded_from_prior_records | false | false | false | `NOT_PROVEN.md`, `V1_0_CLAIM_BOUNDARY.md` |

## Required Fix Plan

### A. Claim Boundary Fix

- State V1.0 production runtime as arithmetic/sum-shaped unless production IR/emitter evidence changes.
- State function/array/recursion work as frontier/template/review evidence where that is the actual path.
- Keep natural language completion in NOT_PROVEN for V1.0.
- Avoid using current-workspace post-package evidence to support V1.0 package claims.

### B. Evidence Pack Fix

- Include raw trace shards, trace manifest, replay manifest, and previous 20K evidence for 50K claims.
- Add `metric_source` to readiness/eval outputs.
- Split fixed scaffold, synthetic fixture, summary accounting, loaded prior records, and raw trace metrics.
- Add replay instructions that use only files included in the review package.

### C. Real Capability Fix

- Add production `FunctionIR`, `ArrayIR`, block/statement/return/call nodes, and recursive function nodes.
- Extend `CEmitter` and `CandidateExecutor` to emit and compile those constructs.
- Add compiler-backed raw traces for generated non-arithmetic programs.
- Add import/reachability tests proving which routers are production, legacy, or experimental.

## Final Verdict

The package is not all failed: bounded runtime evidence, compiler-backed review evidence, and several claim-boundary safeguards exist. However, the strongest production claims need repair. Function, array, and recursion production support are not established by the audited source. Recursion and Turing-frontier evidence should remain frontier/contract/review evidence unless raw recursive C generation and production compiler traces are added. The V1.0 source-review package does not contain enough raw 50K trace material for third-party replay, even though the current workspace has later/raw trace files.
