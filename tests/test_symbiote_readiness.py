from jianmu.self_learning.darwinforge.symbiote_comfort_zone_audit import build_symbiote_data_mix_manifest, run_comfort_zone_audit
from jianmu.self_learning.darwinforge.symbiote_cycle_runner import run_symbiote_cycles
from jianmu.self_learning.darwinforge.symbiote_freeze_thaw_protocol import build_freeze_thaw_protocol
from jianmu.self_learning.darwinforge.symbiote_generalization_audit import run_generalization_audit
from jianmu.self_learning.darwinforge.symbiote_readiness import build_symbiote_readiness
from jianmu.self_learning.darwinforge.symbiote_reward_model import build_symbiote_reward_model
from jianmu.self_learning.darwinforge.symbiote_snapshot import create_symbiote_snapshots


def test_readiness_no_gan_claim(tmp_path):
    result = build_symbiote_readiness(
        create_symbiote_snapshots(tmp_path),
        build_freeze_thaw_protocol(tmp_path),
        build_symbiote_reward_model(tmp_path),
        run_symbiote_cycles(tmp_path),
        run_comfort_zone_audit(tmp_path),
        run_generalization_audit(tmp_path),
        {"compiler_verified_correctness_rate": 1.0, "wrong_stdout_count": 0, "timeout_count": 0, "permission_error_count": 0, "cleanup_failure_count": 0, "boundary_compiler_misroute_count": 0, "future_domain_compiled_count": 0},
        {"charter_guard_passed": True},
        build_symbiote_data_mix_manifest(tmp_path),
        tmp_path,
    )
    assert result["recommended_claim_level"] == "symbiotic_cotraining_positive"
    assert "Turing completeness" in result["still_not_proven"]


def test_readiness_no_production_claim(tmp_path):
    result = build_symbiote_readiness(
        create_symbiote_snapshots(tmp_path),
        build_freeze_thaw_protocol(tmp_path),
        build_symbiote_reward_model(tmp_path),
        run_symbiote_cycles(tmp_path),
        run_comfort_zone_audit(tmp_path),
        run_generalization_audit(tmp_path),
        {"compiler_verified_correctness_rate": 1.0, "wrong_stdout_count": 0, "timeout_count": 0, "permission_error_count": 0, "cleanup_failure_count": 0, "boundary_compiler_misroute_count": 0, "future_domain_compiled_count": 0},
        {"charter_guard_passed": True},
        build_symbiote_data_mix_manifest(tmp_path),
        tmp_path,
    )
    assert "production readiness" in result["still_not_proven"]
