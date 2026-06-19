from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def run_architecture_finalization_self_check(records_root: str | Path, output_records: str | Path) -> Dict[str, Any]:
    root = Path(records_root)
    support = _load(root / "v1_0_8_controlled_support" / "controlled_opt_in_support_readiness.json")
    approval = _load(root / "v1_0_8_1_approval" / "controlled_opt_in_approval_readiness.json")
    coverage = _load(root / "v1_0_7_2_coverage_replay" / "coverage_expansion_readiness.json")
    blockers = []
    result = {
        "architecture_finalization_check_started": True,
        "architecture_finalization_check_completed": True,
        "atomic_policy_bridge_confirmed": support.get("reused_existing_logic") is True,
        "extended_ir_path_confirmed": coverage.get("adapter_reuses_extended_ir") is True or support.get("reused_existing_logic") is True,
        "extended_emitter_path_confirmed": coverage.get("adapter_reuses_extended_emitter") is True or support.get("reused_existing_logic") is True,
        "compiler_backend_confirmed": support.get("real_compiler_invocations", 0) >= 40_000,
        "staged_opt_in_only_entry_confirmed": support.get("explicit_opt_in_required") is True and approval.get("controlled_opt_in_support_approval_recommended") is True,
        "default_profile_unchanged": support.get("default_profile_unchanged") is True and approval.get("default_profile_unchanged") is True,
        "default_profile_bridge_leak_detected": support.get("default_profile_bridge_leak_detected") is True or approval.get("default_profile_bridge_leak_detected") is True,
        "support_scope_codepath_aligned": support.get("support_scope_matrix_generated") is True,
        "unsupported_boundary_still_enforced": support.get("negative_validation_passed") is True and support.get("unsafe_compile_invoked_count") == 0,
        "failure_taxonomy_still_complete": support.get("failure_taxonomy_generated") is True,
        "template_bypass_detected": bool(support.get("direct_template_path_detected", False)),
        "marker_ir_direct_compile_detected": bool(support.get("marker_ir_direct_compile_detected", False)),
        "summary_only_validation_detected": bool(support.get("summary_only_validation_detected", False)),
    }
    for key in [
        "atomic_policy_bridge_confirmed",
        "extended_ir_path_confirmed",
        "extended_emitter_path_confirmed",
        "compiler_backend_confirmed",
        "staged_opt_in_only_entry_confirmed",
        "default_profile_unchanged",
        "support_scope_codepath_aligned",
        "unsupported_boundary_still_enforced",
        "failure_taxonomy_still_complete",
    ]:
        if not result[key]:
            blockers.append(key)
    for key in ["default_profile_bridge_leak_detected", "template_bypass_detected", "marker_ir_direct_compile_detected", "summary_only_validation_detected"]:
        if result[key]:
            blockers.append(key)
    result["blockers"] = blockers
    result["architecture_finalization_passed"] = not blockers
    _write_json(Path(output_records) / "architecture_finalization_self_check.json", result)
    return result


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
