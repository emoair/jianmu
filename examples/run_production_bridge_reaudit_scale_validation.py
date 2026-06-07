from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.extended_bridge_scale_validation import run_extended_bridge_scale_validation
from jianmu.self_learning.darwinforge.production_bridge_reaudit import run_production_bridge_reaudit
from jianmu.self_learning.darwinforge.production_bridge_scale_readiness import build_production_bridge_scale_readiness
from jianmu.self_learning.darwinforge.scale_validation_scheduler import should_run_phase_b


def main() -> None:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    reaudit = run_production_bridge_reaudit(out)
    scheduler = should_run_phase_b(reaudit)
    scale = {"phase_b_started": False, "phase_b_completed": False}
    if scheduler["phase_b_allowed"] and _truthy(args.phase_b_scale_if_reaudit_passes):
        scale = run_extended_bridge_scale_validation(
            out,
            targets={
                "arithmetic": int(args.arithmetic_target),
                "function": int(args.function_target),
                "array": int(args.array_target),
                "function_array": int(args.function_array_target),
                "structured_recursion": int(args.recursion_target),
                "mixed_extended": int(args.mixed_target),
            },
            wall_clock_min_hours=float(args.wall_clock_min_hours),
            max_runtime_hours=float(args.max_runtime_hours),
            hard_stop_hours=float(args.hard_stop_hours),
            minimum_real_compiler_invocations=int(args.minimum_real_compiler_invocations),
        )
    readiness = build_production_bridge_scale_readiness(out, reaudit, scale)
    claim = {
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "ready_for_official_release": False,
        "claim_boundary_still_safe": reaudit.get("claim_boundary_still_safe", False),
    }
    _write_json(out / "claim_boundary_recheck.json", claim)
    _write_mainline(out / "mainline_conclusion.md", reaudit, scale, readiness)
    _write_json(out / "mainline_conclusion.json", {"reaudit": reaudit, "scale": scale, "readiness": readiness})
    print(json.dumps({"output_records": str(out), "phase_a_passed": reaudit["phase_a_passed"], "recommended_claim_level": readiness["recommended_claim_level"]}, ensure_ascii=False, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-5", default="records/v1_0_5_reconciliation")
    parser.add_argument("--output-records", default="records/v1_0_5_1_reaudit_scale")
    parser.add_argument("--phase-a-reaudit", default="true")
    parser.add_argument("--phase-b-scale-if-reaudit-passes", default="true")
    parser.add_argument("--wall-clock-min-hours", default="4")
    parser.add_argument("--max-runtime-hours", default="4")
    parser.add_argument("--hard-stop-hours", default="4.5")
    parser.add_argument("--target-real-compiler-invocations", default="80000")
    parser.add_argument("--minimum-real-compiler-invocations", default="25000")
    parser.add_argument("--arithmetic-target", default="10000")
    parser.add_argument("--function-target", default="15000")
    parser.add_argument("--array-target", default="15000")
    parser.add_argument("--function-array-target", default="15000")
    parser.add_argument("--recursion-target", default="10000")
    parser.add_argument("--mixed-target", default="15000")
    parser.add_argument("--require-extended-ir-path", default="true")
    parser.add_argument("--require-atomic-policy-bridge", default="true")
    parser.add_argument("--forbid-template-bypass", default="true")
    parser.add_argument("--forbid-marker-ir-direct-compile", default="true")
    parser.add_argument("--require-reuse-existing-logic", default="true")
    parser.add_argument("--generate-policy-path-trace", default="true")
    parser.add_argument("--generate-scale-trace-pack", default="true")
    parser.add_argument("--run-compiler-accounting-audit", default="true")
    parser.add_argument("--run-claim-boundary-recheck", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="true")
    parser.add_argument("--seed", default="194,195,196")
    return parser.parse_args()


def _truthy(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def _write_mainline(path: Path, reaudit, scale, readiness) -> None:
    still = "\n".join(f"- {item}" for item in readiness["still_not_proven"])
    blocking = "\n".join(f"- {item}" for item in readiness["blocking_issues"]) or "- none"
    path.write_text(f"""# V1.0.5.1 Production Bridge Reaudit and Scale Validation

## What was reaudited

v1.0.5 ExtendedIR, ExtendedEmitterC, AtomicSynthesis experimental policies, template bypass risk, reuse policy, metric/evidence honesty, and claim boundary safety.

## Phase A

- phase_a_passed: {reaudit.get('phase_a_passed')}
- ExtendedIR to Emitter to Compiler path confirmed: {reaudit.get('function_ir_path_confirmed') and reaudit.get('array_ir_path_confirmed') and reaudit.get('function_array_ir_path_confirmed') and reaudit.get('recursion_ir_path_confirmed')}
- template_bypass_detected: {reaudit.get('template_bypass_detected')}
- marker_ir_direct_compile_detected: {reaudit.get('marker_ir_direct_compile_detected')}
- atomic_policy_bridge_confirmed: {reaudit.get('atomic_policy_bridge_confirmed')}
- reuse_existing_logic_confirmed: {reaudit.get('reuse_existing_logic_confirmed')}
- rewrite_violation_detected: {reaudit.get('rewrite_violation_detected')}

## Phase B

- phase_b_started: {scale.get('phase_b_started')}
- phase_b_completed: {scale.get('phase_b_completed')}
- wall_clock_hours: {scale.get('wall_clock_hours', 0.0)}
- wall_clock_minimum_satisfied: {scale.get('wall_clock_minimum_satisfied', False)}
- real_compiler_invocations: {scale.get('real_compiler_invocations', 0)}
- compiler_verified_correctness_rate: {scale.get('compiler_verified_correctness_rate', 0.0)}

## Policy Compile Results

- arithmetic_regression_compile_success_rate: {scale.get('arithmetic_regression_compile_success_rate', 0.0)}
- function_ir_compile_success_rate: {scale.get('function_ir_compile_success_rate', 0.0)}
- array_ir_compile_success_rate: {scale.get('array_ir_compile_success_rate', 0.0)}
- function_array_ir_compile_success_rate: {scale.get('function_array_ir_compile_success_rate', 0.0)}
- structured_recursion_ir_compile_success_rate: {scale.get('structured_recursion_ir_compile_success_rate', 0.0)}
- mixed_extended_ir_compile_success_rate: {scale.get('mixed_extended_ir_compile_success_rate', 0.0)}

## Claim Boundary

- production_function_support_completed: false
- production_array_support_completed: false
- production_recursion_support_completed: false
- ready_for_official_release: false

## Readiness

- recommended_claim_level: {readiness.get('recommended_claim_level')}
- blocking_issues:
{blocking}

## Required Next Run

{readiness.get('required_next_run')}

## Still Not Proven

{still}
""", encoding="utf-8")


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

