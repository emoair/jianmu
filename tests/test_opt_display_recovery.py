from jianmu.self_learning.darwinforge.opt_display_recovery import recover_opt_display


def test_opt_display_recovery_binds_to_backend_manifest(tmp_path) -> None:
    result = recover_opt_display(tmp_path, {"backend_cl_invocations": 1}, {"security_interference_classification_clean": True}, {"actual_elapsed_seconds": 1})
    assert result["opt_display_bound_to_backend_manifest"] is True


def test_opt_display_not_used_as_correctness_evidence(tmp_path) -> None:
    result = recover_opt_display(tmp_path, {}, {}, {})
    assert result["opt_display_not_used_as_correctness_evidence"] is True

