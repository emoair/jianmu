from jianmu.self_learning.darwinforge.batch_compile_validator import run_batch_compile_validation
import jianmu.self_learning.darwinforge.turing_proof_function_array_frontend_scaleup as scaleup


def test_batch_compile_validator_separate_accounting(tmp_path):
    result = run_batch_compile_validation(tmp_path, target=4, compile_worker_count=2)
    assert result["full_compile_invocation_count"] == 4
    assert result["compiler_verified_correctness_rate"] == 1.0
    assert result["batch_compile_validation_completed"] is True


def test_batch_compile_validator_does_not_mask_failures(tmp_path, monkeypatch):
    def fake_validation(output_records, target=4, compile_worker_count=2):
        return {
            "real_compiler_invocation_count": 4,
            "compiler_verified_correctness_rate": 0.75,
            "wrong_stdout_count": 1,
            "timeout_count": 1,
            "permission_error_count": 0,
            "cleanup_failure_count": 0,
            "boundary_compiler_misroute_count": 0,
            "future_domain_compiled_count": 0,
            "pointer_compiled_count": 0,
            "io_compiled_count": 0,
        }

    monkeypatch.setattr(scaleup, "run_symbiote_compiler_validation", fake_validation)
    result = scaleup.run_batch_compile_validation(tmp_path, target=4, compile_worker_count=2)
    assert result["full_compile_invocation_count"] == 4
    assert result["full_compile_success_count"] == 3
    assert result["runtime_success_count"] == 3
    assert result["stdout_correct_count"] == 3
    assert result["wrong_stdout_count"] == 1
    assert result["timeout_count"] == 1
