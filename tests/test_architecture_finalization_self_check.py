import json

from jianmu.self_learning.darwinforge.architecture_finalization_self_check import run_architecture_finalization_self_check


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_architecture_finalization_confirms_existing_bridge(tmp_path):
    _write(tmp_path / "v1_0_8_controlled_support" / "controlled_opt_in_support_readiness.json", {"reused_existing_logic": True, "real_compiler_invocations": 50000, "explicit_opt_in_required": True, "support_scope_matrix_generated": True, "negative_validation_passed": True, "unsafe_compile_invoked_count": 0, "failure_taxonomy_generated": True, "default_profile_unchanged": True})
    _write(tmp_path / "v1_0_8_1_approval" / "controlled_opt_in_approval_readiness.json", {"controlled_opt_in_support_approval_recommended": True, "default_profile_unchanged": True})
    _write(tmp_path / "v1_0_7_2_coverage_replay" / "coverage_expansion_readiness.json", {"adapter_reuses_extended_ir": True, "adapter_reuses_extended_emitter": True})
    result = run_architecture_finalization_self_check(tmp_path, tmp_path / "out")
    assert result["architecture_finalization_passed"] is True


def test_architecture_finalization_blocks_template_bypass(tmp_path):
    _write(tmp_path / "v1_0_8_controlled_support" / "controlled_opt_in_support_readiness.json", {"reused_existing_logic": True, "real_compiler_invocations": 50000, "explicit_opt_in_required": True, "support_scope_matrix_generated": True, "negative_validation_passed": True, "unsafe_compile_invoked_count": 0, "failure_taxonomy_generated": True, "default_profile_unchanged": True, "direct_template_path_detected": True})
    _write(tmp_path / "v1_0_8_1_approval" / "controlled_opt_in_approval_readiness.json", {"controlled_opt_in_support_approval_recommended": True, "default_profile_unchanged": True})
    _write(tmp_path / "v1_0_7_2_coverage_replay" / "coverage_expansion_readiness.json", {"adapter_reuses_extended_ir": True, "adapter_reuses_extended_emitter": True})
    result = run_architecture_finalization_self_check(tmp_path, tmp_path / "out")
    assert result["architecture_finalization_passed"] is False
