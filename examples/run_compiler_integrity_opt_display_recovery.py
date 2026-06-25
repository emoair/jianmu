from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.backend_compiler_manifest import build_backend_manifest_contract
from jianmu.self_learning.darwinforge.backend_validation_replay import run_backend_replay, run_short_backend_validation
from jianmu.self_learning.darwinforge.compiler_integrity_readiness import build_compiler_integrity_readiness
from jianmu.self_learning.darwinforge.compiler_integrity_schema import BackendValidationConfig, STILL_NOT_PROVEN_COMPILER_INTEGRITY
from jianmu.self_learning.darwinforge.compiler_invocation_integrity_audit import audit_v1_0_8_8_compiler_claim
from jianmu.self_learning.darwinforge.frontend_backend_lane_classifier import classify_frontend_backend_lanes
from jianmu.self_learning.darwinforge.opt_display_recovery import recover_opt_display
from jianmu.self_learning.darwinforge.security_interference_detector import audit_security_interference


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    source_summary = _load(Path(args.source_records_v1_0_8_8) / "endurance_summary.json")
    claim = audit_v1_0_8_8_compiler_claim(args.source_records_v1_0_8_8, out)
    if args.require_cl_exe and not shutil.which("cl"):
        readiness = build_compiler_integrity_readiness(out, {
            **claim,
            "compiler_integrity_audit_completed": True,
            "backend_validation_passed": False,
            "backend_replay_passed": False,
            "frontend_backend_lane_separated": False,
            "backend_manifest_contract_passed": False,
            "opt_display_recovery_passed": False,
            "default_profile_unchanged": True,
            "real_promotion_enabled": False,
            "blocking_issues": ["cl_exe_not_found"],
        })
        write_report(out, readiness)
        return 1
    if args.require_link_exe and not shutil.which("link"):
        readiness = build_compiler_integrity_readiness(out, {
            **claim,
            "compiler_integrity_audit_completed": True,
            "backend_validation_passed": False,
            "backend_replay_passed": False,
            "frontend_backend_lane_separated": False,
            "backend_manifest_contract_passed": False,
            "opt_display_recovery_passed": False,
            "default_profile_unchanged": True,
            "real_promotion_enabled": False,
            "blocking_issues": ["link_exe_not_found"],
        })
        write_report(out, readiness)
        return 1
    cfg = BackendValidationConfig(
        events=args.events,
        minimum_backend_cl_invocations=args.minimum_backend_cl_invocations,
        minimum_backend_link_invocations=args.minimum_backend_link_invocations,
        minimum_backend_exe_runs=args.minimum_backend_exe_runs,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        replay_samples=args.replay_samples,
        replay_minimum_samples=args.replay_minimum_samples,
    )
    backend = run_short_backend_validation(out, cfg)
    rows = [json.loads(line) for line in (out / "backend_invocation_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    contract = build_backend_manifest_contract(out, rows[0] if rows else {})
    security = audit_security_interference(out, rows)
    lanes = classify_frontend_backend_lanes(out, frontend_events=backend["frontend_generated_events"], backend_cl=backend["backend_cl_invocations"], backend_link=backend["backend_link_invocations"], backend_exe=backend["backend_exe_runs"])
    opt = recover_opt_display(out, backend, security, source_summary)
    replay = run_backend_replay(out, cfg)
    payload = {
        **claim,
        **backend,
        **contract,
        **security,
        **lanes,
        **opt,
        **replay,
        "compiler_integrity_audit_completed": True,
        "frontend_backend_lane_separated": lanes["lane_classification_passed"],
        "real_compile_lane_integrity_repaired": backend["backend_validation_passed"] and replay["backend_replay_passed"],
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
    }
    readiness = build_compiler_integrity_readiness(out, payload)
    write_report(out, readiness)
    print(json.dumps({"recommended_claim_level": readiness["recommended_claim_level"], "backend_cl_invocations": readiness.get("backend_cl_invocations")}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] != "failed" else 1


def write_report(out: Path, readiness: dict) -> None:
    lines = [
        "# v1.0.8.8.1 Compiler Invocation Integrity Audit and OPT Display Recovery",
        "",
        "This version audits the v1.0.8.8 compiler invocation claim, separates frontend events from backend compiler verification, restores OPT display/trace, detects security interference, and runs a short real backend validation with cl/link/exe pid, returncode, artifact, timing, and stdout evidence.",
        "",
        "It does not restore v1.0.8.8 backend compiler counts unless per-invocation evidence exists. It does not change the default profile, enable real promotion, release, or claim production support completed.",
        "",
        f"- v1.0.8.8 time claim retained as time-positive: `true`",
        f"- v1.0.8.8 compiler claim accepted: `{readiness.get('v1_0_8_8_compiler_claim_accepted')}`",
        f"- v1.0.8.8 compiler claim downgraded: `{readiness.get('v1_0_8_8_compiler_claim_downgraded')}`",
        f"- downgrade reason: `{readiness.get('downgrade_reason')}`",
        f"- frontend/backend lane separated: `{readiness.get('frontend_backend_lane_separated')}`",
        f"- backend manifest contract passed: `{readiness.get('backend_manifest_contract_passed')}`",
        f"- OPT display recovered: `{readiness.get('opt_display_recovery_passed')}`",
        f"- security interference detected count: `{readiness.get('security_interference_detected_count')}`",
        f"- backend validation passed: `{readiness.get('backend_validation_passed')}`",
        f"- backend replay passed: `{readiness.get('backend_replay_passed')}`",
        f"- default profile unchanged: `{readiness.get('default_profile_unchanged')}`",
        f"- real promotion enabled: `{readiness.get('real_promotion_enabled')}`",
        f"- production support completed: `false`",
        f"- recommended claim level: `{readiness.get('recommended_claim_level')}`",
        f"- blocking issues: `{readiness.get('blocking_issues')}`",
        f"- required next run: `{readiness.get('required_next_run')}`",
        "",
        "## Still Not Proven",
        "",
    ]
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN_COMPILER_INTEGRITY)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN_COMPILER_INTEGRITY)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-8-8", default="records/v1_0_8_8_mirror_redqueen_8h")
    parser.add_argument("--output-records", default="records/v1_0_8_8_1_compiler_integrity")
    parser.add_argument("--events", type=int, default=30000)
    parser.add_argument("--minimum-backend-cl-invocations", type=int, default=15000)
    parser.add_argument("--minimum-backend-link-invocations", type=int, default=15000)
    parser.add_argument("--minimum-backend-exe-runs", type=int, default=15000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--replay-samples", type=int, default=1000)
    parser.add_argument("--replay-minimum-samples", type=int, default=500)
    parser.add_argument("--seed", default="246,247,248")
    for flag in ["audit-v1-0-8-8-compiler-claim", "separate-frontend-backend-lanes", "require-backend-manifest", "record-cl-pid", "record-link-pid", "record-exe-pid", "record-returncodes", "record-artifacts", "record-stdout-comparison", "record-subprocess-monotonic-timing", "security-interference-detection", "detect-antivirus-360", "opt-display-recovery", "opt-trace-manifest", "opt-display-bind-backend-manifest", "opt-display-bind-trace", "run-short-backend-validation", "trace-writer-mode", "temp-dir-mode", "accounting-lock", "use-msvc-preflight", "require-cl-exe", "require-link-exe", "run-backend-replay", "no-model-training", "no-weight-update", "explicit-opt-in-required", "forbid-default-profile-change", "forbid-real-promotion", "forbid-release", "require-v1-0-6-adapter-reuse", "require-atomic-policy-bridge", "require-extended-ir-path", "require-extended-emitter", "forbid-template-bypass", "forbid-marker-ir-direct-compile", "forbid-summary-only-validation", "run-claim-boundary-review", "run-architecture-charter-guard", "progress"]:
        parser.add_argument(f"--{flag}", type=_bool, default=True)
    return parser.parse_args()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())

