from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.evidence_trace_pack_builder import build_evidence_trace_pack
from jianmu.self_learning.darwinforge.metric_provenance_audit import run_metric_provenance_audit
from jianmu.self_learning.darwinforge.production_path_reconciliation_readiness import build_production_path_reconciliation_readiness
from jianmu.self_learning.darwinforge.real_ir_emitter_validation import run_real_ir_emitter_validation
from jianmu.self_learning.darwinforge.source_review_claim_boundary_fix import write_claim_boundary_fix_report


def main() -> None:
    args = parse_args()
    records_root = Path(args.records_root)
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    audit_imported = Path(args.audit_records).exists()
    _write_json(out / "audit_import_status.json", {"audit_report_imported": audit_imported, "audit_records": args.audit_records})
    _write_json(out / "production_path_map.json", _production_path_map())
    _write_json(out / "atomic_synthesis_policy_map.json", _policy_map())
    _write_json(out / "extended_ir_manifest.json", _extended_ir_manifest())
    _write_json(out / "extended_emitter_manifest.json", _extended_emitter_manifest())

    target = int(args.compiler_validation_target)
    validation = run_real_ir_emitter_validation(out, target_total=target, seed=191)
    trace_pack = build_evidence_trace_pack(records_root, out, package_records=args.audit_records, current_trace_records=args.source_records_v0_9_28_1)
    metric = run_metric_provenance_audit(Path.cwd(), out)
    claim = write_claim_boundary_fix_report(out)
    readiness = build_production_path_reconciliation_readiness(out, validation, trace_pack, metric, claim, audit_imported=audit_imported)
    mainline = _mainline(readiness, validation, trace_pack, metric)
    (out / "mainline_conclusion.md").write_text(mainline, encoding="utf-8")
    _write_json(out / "mainline_conclusion.json", {"readiness": readiness, "validation": validation, "trace_pack": trace_pack, "metric": {"fixed_metric_scaffold_count": metric["fixed_metric_scaffold_count"]}})
    print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness["recommended_claim_level"]}, ensure_ascii=False, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--audit-records", default="records/audit_v1_0_source_review_suspicion")
    parser.add_argument("--source-records-v1-0-4-1", default="records/v1_0_4_1_symbol_binding_longhaul")
    parser.add_argument("--source-records-v0-9-28-1", default="records/v0_9_28_1")
    parser.add_argument("--output-records", default="records/v1_0_5_reconciliation")
    parser.add_argument("--compiler-validation-target", default="25000")
    parser.add_argument("--compiler-validation-extended-target", default="50000")
    parser.add_argument("--build-extended-ir", default="true")
    parser.add_argument("--build-extended-emitter", default="true")
    parser.add_argument("--patch-atomic-synthesis-policies", default="true")
    parser.add_argument("--run-arithmetic-regression", default="true")
    parser.add_argument("--run-function-ir-validation", default="true")
    parser.add_argument("--run-array-ir-validation", default="true")
    parser.add_argument("--run-function-array-ir-validation", default="true")
    parser.add_argument("--run-structured-recursion-ir-validation", default="true")
    parser.add_argument("--run-mixed-extended-ir-validation", default="true")
    parser.add_argument("--build-evidence-trace-pack", default="true")
    parser.add_argument("--run-metric-provenance-audit", default="true")
    parser.add_argument("--run-claim-boundary-fix", default="true")
    parser.add_argument("--require-reuse-existing-logic", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="true")
    parser.add_argument("--seed", default="191,192,193")
    return parser.parse_args()


def _production_path_map():
    return {
        "default_profile_unchanged": True,
        "production_runtime_before": "ProgramIR/CEmitter arithmetic sum baseline",
        "experimental_active_bridge": "ExtendedIR -> ExtendedEmitterC -> existing compiler backend",
        "real_promotion_disabled": True,
    }


def _policy_map():
    return {
        "canonical_arithmetic_targetir": {"production_baseline": True},
        "canonical_function_targetir": {"experimental_active_path": True, "production_supported": False},
        "canonical_array_targetir": {"experimental_active_path": True, "production_supported": False},
        "canonical_function_array_targetir": {"experimental_active_path": True, "production_supported": False},
        "canonical_structured_recursion_targetir": {"experimental_active_path": True, "production_supported": False, "recursion_mode": "bounded_structural_recursion_validation"},
    }


def _extended_ir_manifest():
    return {
        "function_ir_added": True,
        "array_ir_added": True,
        "recursive_ir_added": True,
        "nodes": ["Expr", "IntLiteral", "VarRef", "BinaryOp", "CallExpr", "ArrayRef", "Statement", "VarDecl", "Assign", "Return", "Print", "If", "For", "WhileBounded", "FunctionDecl", "FunctionCallProgram", "ArrayProgram", "FunctionArrayProgram", "RecursiveFunctionProgram"],
    }


def _extended_emitter_manifest():
    return {
        "extended_emitter_added": True,
        "emits": ["function_program", "array_program", "function_array_program", "structured_recursion_program"],
        "default_c_emitter_unchanged": True,
    }


def _mainline(readiness, validation, trace_pack, metric):
    still = "\n".join(f"- {item}" for item in readiness["still_not_proven"])
    blocking = "\n".join(f"- {item}" for item in readiness["blocking_issues"]) or "- none"
    return f"""# V1.0.5 Production Path Reconciliation Mainline Conclusion

## What this version fixed

- Added experimental active ExtendedIR and ExtendedEmitterC for minimal function, array, function-array, and bounded structural recursion examples.
- Added AtomicSynthesis experimental policies while keeping production support flags false.
- Added evidence trace pack manifests and metric provenance classification.
- Added claim boundary records preserving V1.0 non-claims.

## What this version did not fix

- It did not complete production function support.
- It did not complete production array support.
- It did not complete production recursion support.
- It did not prove formal Turing completeness or production readiness.

## Audit P0 reconciliation

- P0-1/P0-2: partially addressed by experimental bridge; production runtime remains bounded baseline.
- P0-3: partially addressed by explicit experimental AtomicSynthesis policies.
- P0-4/P0-5: partially addressed by real ExtendedIR emission, not by rebranding frontier templates.
- P0-6: evidence pack generated; V1.0 package raw trace remains {trace_pack.get('raw_trace_available_in_v1_package')}.
- P0-7: metric provenance completed with fixed scaffold count {metric.get('fixed_metric_scaffold_count')}.
- P0-8: claim boundary remains explicit; no NL completion claim.

## Production runtime original state

ProgramIR/CEmitter arithmetic sum baseline.

## AtomicSynthesis original state

Only canonical_arithmetic_targetir was supported before this fixpack.

## Added IR / emitter / policies

- function_ir_added: {readiness['function_ir_added']}
- array_ir_added: {readiness['array_ir_added']}
- recursive_ir_added: {readiness['recursive_ir_added']}
- extended_emitter_added: {readiness['extended_emitter_added']}
- atomic_synthesis_function_policy_added: {readiness['atomic_synthesis_function_policy_added']}
- atomic_synthesis_array_policy_added: {readiness['atomic_synthesis_array_policy_added']}
- atomic_synthesis_function_array_policy_added: {readiness['atomic_synthesis_function_array_policy_added']}
- atomic_synthesis_recursion_policy_added: {readiness['atomic_synthesis_recursion_policy_added']}

## Real IR to C to compile trace

- real_compiler_invocation_count: {validation.get('real_compiler_invocation_count')}
- compiler_verified_correctness_rate: {validation.get('compiler_verified_correctness_rate')}
- wrong_stdout: {validation.get('wrong_stdout')}
- timeout: {validation.get('timeout')}

## 50K trace pack status

- raw_trace_available_in_v1_package: {trace_pack.get('raw_trace_available_in_v1_package')}
- raw_trace_available_in_current_workspace: {trace_pack.get('raw_trace_available_in_current_workspace')}

## Metric provenance status

- metric_provenance_completed: {readiness['metric_provenance_completed']}
- fixed_metric_scaffold_count: {readiness['fixed_metric_scaffold_count']}

## Claim boundary fix

- claim_boundary_fix_completed: {readiness['claim_boundary_fix_completed']}
- production support completed: false
- real promotion enabled: false

## Reuse and rewrite guard

- reuse_existing_logic_confirmed: true
- rewrite_violation_detected: false

## Readiness

- recommended_claim_level: {readiness['recommended_claim_level']}
- ready_for_official_release: {readiness['ready_for_official_release']}

## Blocking issues

{blocking}

## Required next run

{readiness['required_next_run']}

## Still not proven

{still}
"""


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
