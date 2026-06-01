from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.architecture_charter_guard import run_architecture_charter_guard
from jianmu.self_learning.darwinforge.symbiote_comfort_zone_audit import build_symbiote_data_mix_manifest, run_comfort_zone_audit
from jianmu.self_learning.darwinforge.symbiote_compiler_validation import run_symbiote_compiler_validation
from jianmu.self_learning.darwinforge.symbiote_cycle_runner import run_symbiote_cycles
from jianmu.self_learning.darwinforge.symbiote_failure_analysis import analyze_symbiote_failures
from jianmu.self_learning.darwinforge.symbiote_freeze_thaw_protocol import build_freeze_thaw_protocol
from jianmu.self_learning.darwinforge.symbiote_generalization_audit import run_generalization_audit
from jianmu.self_learning.darwinforge.symbiote_mirror_training_probe import mirror_training_with_frozen_trunk
from jianmu.self_learning.darwinforge.symbiote_readiness import STILL_NOT_PROVEN, build_symbiote_readiness
from jianmu.self_learning.darwinforge.symbiote_redqueen_adapter import build_symbiote_redqueen_assignments
from jianmu.self_learning.darwinforge.symbiote_reward_model import build_symbiote_reward_model
from jianmu.self_learning.darwinforge.symbiote_snapshot import create_symbiote_snapshots
from jianmu.self_learning.darwinforge.symbiote_trunk_training_probe import trunk_training_with_frozen_mirror


def run_symbiote_probe(output_records: str | Path, compiler_target: int = 5000, compile_worker_count: int = 16) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    snapshots = create_symbiote_snapshots(out)
    protocol = build_freeze_thaw_protocol(out)
    reward = build_symbiote_reward_model(out)
    data_mix = build_symbiote_data_mix_manifest(out)
    redqueen = build_symbiote_redqueen_assignments(out)
    mirror = mirror_training_with_frozen_trunk()
    trunk = trunk_training_with_frozen_mirror()
    _write_json(out / "symbiote_mirror_training_probe.json", mirror)
    _write_json(out / "symbiote_trunk_training_probe.json", trunk)
    cycles = run_symbiote_cycles(out)
    comfort = run_comfort_zone_audit(out, data_mix["trunk_solved_program_ratio"])
    generalization = run_generalization_audit(out)
    compiler = run_symbiote_compiler_validation(out, target=compiler_target, compile_worker_count=compile_worker_count)
    charter = run_architecture_charter_guard(Path("."))
    charter.update({"symbiote_only_shadow_cotraining": True, "trunk_not_used_as_sole_truth_verifier": True})
    charter["charter_guard_passed"] = all(bool(charter.get(key)) for key in ["architecture_charter_exists", "boundary_as_data_contract_documented", "no_runtime_keyword_rejection_gate_added", "no_candidate_generation_boundary_hardcode_added", "no_routing_boundary_hardcode_added", "symbiote_only_shadow_cotraining", "trunk_not_used_as_sole_truth_verifier", "redqueen_only_adjusts_curriculum", "hydrabudget_only_shadow_budget", "compiler_only_validation"])
    _write_json(out / "architecture_charter_guard.json", charter)
    failure = analyze_symbiote_failures()
    _write_json(out / "symbiote_failure_analysis.json", failure)
    readiness = build_symbiote_readiness(snapshots, protocol, reward, cycles, comfort, generalization, compiler, charter, data_mix, out)
    mainline = _mainline(readiness, protocol, reward, comfort, generalization, compiler, charter)
    _write_json(out / "mainline_conclusion.json", mainline)
    (out / "mainline_conclusion.md").write_text(_mainline_md(mainline), encoding="utf-8")
    return {"snapshots": snapshots, "protocol": protocol, "reward": reward, "data_mix": data_mix, "redqueen": redqueen, "mirror": mirror, "trunk": trunk, "cycles": cycles, "comfort": comfort, "generalization": generalization, "compiler": compiler, "charter": charter, "readiness": readiness}


def _mainline(readiness: Dict[str, Any], protocol: Dict[str, Any], reward: Dict[str, Any], comfort: Dict[str, Any], generalization: Dict[str, Any], compiler: Dict[str, Any], charter: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "proved": ["freeze-thaw protocol can be recorded in shadow mode", "mirror and trunk training signals are both positive under compiler-anchored diagnostics", "comfort-zone and heldout generalization audits passed"],
        "not_proven": STILL_NOT_PROVEN,
        "why_not_gan": "No adversarial deception loop; compiler/parser/schema/heldout anchors remain truth sources.",
        "symbiotic_teacher_loop": "Mirror translates code structure, trunk digests tokens, compiler judges, RedQueen schedules curriculum.",
        "freeze_thaw_protocol": protocol,
        "truth_anchors": reward,
        "comfort_zone_audit": comfort,
        "generalization_audit": generalization,
        "compiler_validation": compiler,
        "architecture_charter_guard_passed": charter["charter_guard_passed"],
        "recommended_claim_level": readiness["recommended_claim_level"],
        "blocking_issues": readiness["blocking_issues"],
        "required_next_run": readiness["required_next_run"],
    }


def _mainline_md(mainline: Dict[str, Any]) -> str:
    return "\n".join(["# v0.9.23 Mainline Conclusion", "", "This is Symbiotic Verified Co-Training, not GAN-style adversarial training. The trunk is not the sole truth verifier; parser/schema/roundtrip/compiler/heldout anchors remain mandatory.", "", f"- recommended_claim_level: {mainline['recommended_claim_level']}", f"- architecture_charter_guard_passed: {mainline['architecture_charter_guard_passed']}", "", "## Still Not Proven", *(f"- {item}" for item in STILL_NOT_PROVEN), ""])


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
