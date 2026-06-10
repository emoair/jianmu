from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.dry_run_execution_harness import run_dry_run_execution
from jianmu.self_learning.darwinforge.dry_run_profile_guard import run_dry_run_profile_guard
from jianmu.self_learning.darwinforge.dry_run_regression_guard import run_dry_run_regression_guard
from jianmu.self_learning.darwinforge.dry_run_rollback_audit import run_dry_run_rollback_audit
from jianmu.self_learning.darwinforge.production_profile_dry_run_readiness import build_production_profile_dry_run_readiness
from jianmu.self_learning.darwinforge.production_profile_dry_run_schema import ProductionProfileDryRunConfig, STILL_NOT_PROVEN
from jianmu.self_learning.darwinforge.production_profile_interface_adapter import audit_interface_adapter
from jianmu.self_learning.darwinforge.shadow_profile_config import build_shadow_profile_config


def main() -> int:
    args = _parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    cfg = ProductionProfileDryRunConfig(
        profile_name=args.profile_name,
        explicitly_opt_in=args.explicit_opt_in,
        real_promotion_enabled=False,
        user_facing_enabled=False,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        trace_writer_mode=args.trace_writer_mode,
        temp_dir_mode=args.temp_dir_mode,
        accounting_lock=args.accounting_lock,
    )
    shadow = build_shadow_profile_config(out, cfg)
    guard = run_dry_run_profile_guard(out, shadow)
    adapter = audit_interface_adapter(out)
    regression = run_dry_run_regression_guard(out, cfg)
    rollback = run_dry_run_rollback_audit(out, cfg)
    if not guard.get("dry_run_profile_guard_passed"):
        execution = {
            "production_dry_run_executed": False,
            "trace_pack_generated": False,
            "trace_pack_replayable": False,
            "blocking_issues": ["guard_failed"],
        }
    else:
        targets = cfg.target_counts(
            arithmetic_target=args.arithmetic_target,
            function_target=args.function_target,
            array_target=args.array_target,
            function_array_target=args.function_array_target,
            recursion_target=args.recursion_target,
            mixed_target=args.mixed_target,
        )
        execution = run_dry_run_execution(
            out,
            cfg,
            targets,
            wall_clock_min_hours=args.wall_clock_min_hours,
            max_runtime_hours=args.max_runtime_hours,
            hard_stop_hours=args.hard_stop_hours,
            minimum_real_compiler_invocations=args.minimum_real_compiler_invocations,
            seed=_first_seed(args.seed),
            progress=args.progress,
        )
    readiness = build_production_profile_dry_run_readiness(out, shadow, guard, adapter, execution, regression, rollback)
    _write_mainline(out, readiness, shadow, adapter, execution, regression, rollback)
    print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness["recommended_claim_level"], "real_compiler_invocations": readiness["real_compiler_invocations"]}, ensure_ascii=False, sort_keys=True))
    return 0


def _write_mainline(out: Path, readiness: dict, shadow: dict, adapter: dict, execution: dict, regression: dict, rollback: dict) -> None:
    lines = [
        "# v1.0.6 Production Profile Dry-run Candidate",
        "",
        "## What This Version Did",
        "Created an explicit opt-in shadow production-profile dry-run candidate for the already-reviewed experimental bridge.",
        "",
        "## What This Version Did Not Do",
        "It did not modify the default profile, enable real promotion, claim production support, tag, release, add natural language capability, or add a new frontier.",
        "",
        "## Mainline Result",
        f"- shadow_profile_name: {readiness['shadow_profile_name']}",
        f"- default_profile_unchanged: {readiness['default_profile_unchanged']}",
        f"- real_promotion_enabled: {readiness['real_promotion_enabled']}",
        f"- dry_run_profile_guard_passed: {readiness['dry_run_profile_guard_passed']}",
        f"- adapter_reuses_atomic_policy_bridge: {adapter.get('adapter_reuses_atomic_policy_bridge')}",
        f"- adapter_reuses_extended_ir: {adapter.get('adapter_reuses_extended_ir')}",
        f"- adapter_reuses_extended_emitter: {adapter.get('adapter_reuses_extended_emitter')}",
        f"- direct_template_path_detected: {adapter.get('direct_template_path_detected')}",
        f"- marker_ir_direct_compile_detected: {adapter.get('marker_ir_direct_compile_detected')}",
        f"- real_compiler_invocations: {readiness['real_compiler_invocations']}",
        f"- wall_clock_hours: {readiness['wall_clock_hours']}",
        f"- arithmetic_regression_compile_success_rate: {readiness['arithmetic_regression_compile_success_rate']}",
        f"- function_dry_run_success_rate: {readiness['function_dry_run_success_rate']}",
        f"- array_dry_run_success_rate: {readiness['array_dry_run_success_rate']}",
        f"- function_array_dry_run_success_rate: {readiness['function_array_dry_run_success_rate']}",
        f"- structured_recursion_dry_run_success_rate: {readiness['structured_recursion_dry_run_success_rate']}",
        f"- mixed_dry_run_success_rate: {readiness['mixed_dry_run_success_rate']}",
        f"- regression_guard_passed: {regression.get('regression_guard_passed')}",
        f"- rollback_test_passed: {rollback.get('rollback_test_passed')}",
        f"- trace_pack_replayable: {readiness['trace_pack_replayable']}",
        f"- ready_for_controlled_profile_review: {readiness['ready_for_controlled_profile_review']}",
        f"- production_function_support_completed: {readiness['production_function_support_completed']}",
        f"- production_array_support_completed: {readiness['production_array_support_completed']}",
        f"- production_recursion_support_completed: {readiness['production_recursion_support_completed']}",
        f"- recommended_claim_level: {readiness['recommended_claim_level']}",
        f"- blocking_issues: {readiness['blocking_issues']}",
        f"- required_next_run: {readiness['required_next_run']}",
        "",
        "## Still Not Proven",
    ]
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "shadow_profile": shadow, "adapter": adapter, "execution": execution, "regression": regression, "rollback": rollback}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _first_seed(value: str) -> int:
    return int(str(value).split(",", 1)[0])


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-5-1", default="records/v1_0_5_1_reaudit_scale")
    parser.add_argument("--source-records-v1-0-5-2", default="records/v1_0_5_2_human_review_pack")
    parser.add_argument("--output-records", default="records/v1_0_6_dry_run")
    parser.add_argument("--profile-name", default="production_shadow_dry_run_v1_0_6")
    parser.add_argument("--dry-run", type=_bool, default=True)
    parser.add_argument("--shadow-profile", type=_bool, default=True)
    parser.add_argument("--explicit-opt-in", type=_bool, default=True)
    parser.add_argument("--forbid-default-profile-change", type=_bool, default=True)
    parser.add_argument("--forbid-real-promotion", type=_bool, default=True)
    parser.add_argument("--forbid-user-facing-enable", type=_bool, default=True)
    parser.add_argument("--require-rollback-audit", type=_bool, default=True)
    parser.add_argument("--wall-clock-min-hours", type=float, default=4.0)
    parser.add_argument("--max-runtime-hours", type=float, default=4.0)
    parser.add_argument("--hard-stop-hours", type=float, default=4.5)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    parser.add_argument("--accounting-lock", type=_bool, default=True)
    parser.add_argument("--target-real-compiler-invocations", type=int, default=120000)
    parser.add_argument("--minimum-real-compiler-invocations", type=int, default=40000)
    parser.add_argument("--arithmetic-target", type=int, default=20000)
    parser.add_argument("--function-target", type=int, default=20000)
    parser.add_argument("--array-target", type=int, default=20000)
    parser.add_argument("--function-array-target", type=int, default=20000)
    parser.add_argument("--recursion-target", type=int, default=15000)
    parser.add_argument("--mixed-target", type=int, default=25000)
    parser.add_argument("--require-all-categories", type=_bool, default=True)
    parser.add_argument("--require-atomic-policy-bridge", type=_bool, default=True)
    parser.add_argument("--require-extended-ir-path", type=_bool, default=True)
    parser.add_argument("--require-extended-emitter", type=_bool, default=True)
    parser.add_argument("--forbid-template-bypass", type=_bool, default=True)
    parser.add_argument("--forbid-marker-ir-direct-compile", type=_bool, default=True)
    parser.add_argument("--forbid-summary-only-validation", type=_bool, default=True)
    parser.add_argument("--run-regression-guard", type=_bool, default=True)
    parser.add_argument("--run-rollback-audit", type=_bool, default=True)
    parser.add_argument("--run-trace-pack-builder", type=_bool, default=True)
    parser.add_argument("--run-claim-boundary-review", type=_bool, default=True)
    parser.add_argument("--run-architecture-charter-guard", type=_bool, default=True)
    parser.add_argument("--progress", type=_bool, default=False)
    parser.add_argument("--seed", default="198")
    return parser.parse_args()


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
