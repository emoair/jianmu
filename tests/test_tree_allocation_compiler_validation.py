from __future__ import annotations

from examples import run_access_aware_tree_allocation_dataset_sufficiency_audit as runner


def test_compiler_validation_only_for_reference_and_best_profile(monkeypatch, tmp_path) -> None:
    called = []

    def fake_validation(output_dir, supported, boundary, compile_worker_count=16):
        called.append(output_dir.name)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "compiler_validation_trace_000.jsonl").write_text("{}\n", encoding="utf-8")
        return {
            "backend_type": "real_c_compiler",
            "compiler_name": "cl",
            "compiler_environment": "msvc_vcvars64",
            "real_compiler_invocation_count": len(supported),
            "compiler_verified_correct_rate": 1.0,
            "boundary_compiler_misroute_count": 0,
            "future_domain_compiled_count": 0,
            "recursion_compiled_count": 0,
            "array_compiled_count": 0,
            "function_compiled_count": 0,
            "permission_error_count": 0,
            "cleanup_failure_count": 0,
            "timeout_count": 0,
            "backend_claim_safe": True,
        }

    monkeypatch.setattr(runner, "run_targeted_compiler_validation", fake_validation)
    result = runner.run_access_aware_tree_allocation_dataset_sufficiency_audit(
        "datasets/v0_9_9_turing_frontier_curriculum",
        "records/v0_9_12",
        tmp_path,
        ["allocation-audit"],
        samples=20,
        boundary_samples=20,
        run_compiler_validation=True,
        progress=False,
    )
    assert called == ["current_1B_reference", "hot_rebalanced_1B"]
    assert result["compiler"]["compiler_validation_completed"] is True
