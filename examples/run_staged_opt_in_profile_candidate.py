from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.opt_in_default_blocking_audit import run_opt_in_default_blocking_audit
from jianmu.self_learning.darwinforge.opt_in_execution_harness import run_opt_in_execution
from jianmu.self_learning.darwinforge.opt_in_profile_adapter import audit_opt_in_adapter
from jianmu.self_learning.darwinforge.opt_in_regression_guard import run_opt_in_regression_guard
from jianmu.self_learning.darwinforge.opt_in_rollback_audit import run_opt_in_rollback_audit
from jianmu.self_learning.darwinforge.staged_opt_in_config import build_staged_opt_in_config
from jianmu.self_learning.darwinforge.staged_opt_in_guard import run_staged_opt_in_guard
from jianmu.self_learning.darwinforge.staged_opt_in_profile_schema import STILL_NOT_PROVEN, StagedOptInProfileConfig
from jianmu.self_learning.darwinforge.staged_opt_in_readiness import build_staged_opt_in_readiness


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    cfg = StagedOptInProfileConfig(profile_name=args.profile_name, workers=args.workers, compiler_workers=args.compiler_workers, trace_writer_mode=args.trace_writer_mode, temp_dir_mode=args.temp_dir_mode, accounting_lock=args.accounting_lock)
    config = build_staged_opt_in_config(out, cfg)
    guard = run_staged_opt_in_guard(out, config)
    blocking = run_opt_in_default_blocking_audit(out)
    adapter = audit_opt_in_adapter(out)
    regression = run_opt_in_regression_guard(out)
    if not guard.get("staged_opt_in_guard_passed"):
        execution = {"staged_opt_in_executed": False}
        rollback = {"opt_in_rollback_passed": False}
    elif blocking.get("default_profile_bridge_leak_detected"):
        execution = {"staged_opt_in_executed": False}
        rollback = {"opt_in_rollback_passed": False}
    else:
        targets = cfg.target_counts(args.default_blocking_target, args.arithmetic_target, args.function_target, args.array_target, args.function_array_target, args.recursion_target, args.mixed_target, args.opt_out_rollback_target)
        execution = run_opt_in_execution(out, cfg, targets, args.wall_clock_min_hours, args.max_runtime_hours, args.hard_stop_hours, args.minimum_real_validation_events, _first_seed(args.seed), progress=args.progress)
        rollback = run_opt_in_rollback_audit(out, args.opt_in_rollback_cycles, args.samples_per_rollback_cycle)
    readiness = build_staged_opt_in_readiness(out, config, guard, blocking, adapter, execution, rollback, regression)
    write_mainline(out, readiness)
    print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness["recommended_claim_level"], "real_validation_events": readiness["real_validation_events"]}, ensure_ascii=False, sort_keys=True))
    return 0


def write_mainline(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.7 Staged Opt-in Profile Candidate",
        "",
        "## What This Version Did",
        "Created and validated an explicit staged opt-in profile candidate for the experimental FunctionIR / ArrayIR / FunctionArrayIR / StructuredRecursion bridge.",
        "",
        "## What This Version Did Not Do",
        "It did not change the default profile, enable real promotion, enable official release, claim production support, add natural language, or add a new capability frontier.",
        "",
        "## Mainline Result",
    ]
    for key in [
        "staged_opt_in_profile_name",
        "default_profile_unchanged",
        "explicit_opt_in_required",
        "real_promotion_enabled",
        "user_facing_enabled",
        "staged_opt_in_guard_passed",
        "default_blocking_passed",
        "default_profile_bridge_leak_detected",
        "adapter_reuses_v1_0_6_dry_run_adapter",
        "adapter_reuses_atomic_policy_bridge",
        "adapter_reuses_extended_ir",
        "adapter_reuses_extended_emitter",
        "direct_template_path_detected",
        "real_validation_events",
        "real_compiler_invocations",
        "arithmetic_regression_compile_success_rate",
        "function_opt_in_success_rate",
        "array_opt_in_success_rate",
        "function_array_opt_in_success_rate",
        "structured_recursion_opt_in_success_rate",
        "mixed_opt_in_success_rate",
        "opt_out_rollback_success_rate",
        "opt_in_rollback_passed",
        "regression_guard_passed",
        "trace_pack_replayable",
        "ready_for_controlled_opt_in_support_review",
        "production_function_support_completed",
        "production_array_support_completed",
        "production_recursion_support_completed",
        "recommended_claim_level",
        "blocking_issues",
        "required_next_run",
    ]:
        lines.append(f"- {key}: {readiness.get(key)}")
    lines.extend(["", "## Still Not Proven"])
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--records-root", default="records")
    p.add_argument("--docs-root", default="docs")
    p.add_argument("--source-records-v1-0-5-1", default="records/v1_0_5_1_reaudit_scale")
    p.add_argument("--source-records-v1-0-5-2", default="records/v1_0_5_2_human_review_pack")
    p.add_argument("--source-records-v1-0-6", default="records/v1_0_6_dry_run")
    p.add_argument("--source-records-v1-0-6-1", default="records/v1_0_6_1_controlled_review")
    p.add_argument("--output-records", default="records/v1_0_7_staged_opt_in")
    p.add_argument("--profile-name", default="staged_opt_in_function_array_recursion_v1_0_7")
    p.add_argument("--staged-opt-in-candidate", type=_bool, default=True)
    p.add_argument("--explicit-opt-in-required", type=_bool, default=True)
    p.add_argument("--forbid-default-profile-change", type=_bool, default=True)
    p.add_argument("--forbid-default-bridge-leak", type=_bool, default=True)
    p.add_argument("--forbid-real-promotion", type=_bool, default=True)
    p.add_argument("--forbid-user-facing-enable", type=_bool, default=True)
    p.add_argument("--forbid-release", type=_bool, default=True)
    p.add_argument("--require-rollback-audit", type=_bool, default=True)
    p.add_argument("--wall-clock-min-hours", type=float, default=4.0)
    p.add_argument("--max-runtime-hours", type=float, default=4.0)
    p.add_argument("--hard-stop-hours", type=float, default=4.5)
    p.add_argument("--workers", type=int, default=16)
    p.add_argument("--compiler-workers", type=int, default=16)
    p.add_argument("--trace-writer-mode", default="sharded")
    p.add_argument("--temp-dir-mode", default="per_sample")
    p.add_argument("--accounting-lock", type=_bool, default=True)
    p.add_argument("--target-real-validation-events", type=int, default=130000)
    p.add_argument("--minimum-real-validation-events", type=int, default=45000)
    p.add_argument("--default-blocking-target", type=int, default=5000)
    p.add_argument("--arithmetic-target", type=int, default=15000)
    p.add_argument("--function-target", type=int, default=20000)
    p.add_argument("--array-target", type=int, default=20000)
    p.add_argument("--function-array-target", type=int, default=20000)
    p.add_argument("--recursion-target", type=int, default=15000)
    p.add_argument("--mixed-target", type=int, default=25000)
    p.add_argument("--opt-out-rollback-target", type=int, default=10000)
    p.add_argument("--opt-in-rollback-cycles", type=int, default=200)
    p.add_argument("--samples-per-rollback-cycle", type=int, default=5)
    p.add_argument("--require-all-categories", type=_bool, default=True)
    p.add_argument("--require-v1-0-6-adapter-reuse", type=_bool, default=True)
    p.add_argument("--require-atomic-policy-bridge", type=_bool, default=True)
    p.add_argument("--require-extended-ir-path", type=_bool, default=True)
    p.add_argument("--require-extended-emitter", type=_bool, default=True)
    p.add_argument("--forbid-template-bypass", type=_bool, default=True)
    p.add_argument("--forbid-marker-ir-direct-compile", type=_bool, default=True)
    p.add_argument("--forbid-summary-only-validation", type=_bool, default=True)
    p.add_argument("--run-default-blocking-audit", type=_bool, default=True)
    p.add_argument("--run-regression-guard", type=_bool, default=True)
    p.add_argument("--run-opt-in-rollback-audit", type=_bool, default=True)
    p.add_argument("--run-trace-pack-builder", type=_bool, default=True)
    p.add_argument("--run-claim-boundary-review", type=_bool, default=True)
    p.add_argument("--run-architecture-charter-guard", type=_bool, default=True)
    p.add_argument("--progress", type=_bool, default=False)
    p.add_argument("--seed", default="204")
    return p.parse_args()


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() in {"1", "true", "yes", "on"}


def _first_seed(value: str) -> int:
    return int(str(value).split(",", 1)[0])


if __name__ == "__main__":
    raise SystemExit(main())
