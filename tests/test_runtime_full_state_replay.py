from jianmu.self_learning.darwinforge.runtime_full_state_builder import build_runtime_full_state
from jianmu.self_learning.darwinforge.runtime_full_state_replay import run_cross_process_runtime_reload_eval


def test_runtime_full_state_replay_cross_process(tmp_path):
    build_runtime_full_state(
        {
            "runtime_capture_passed": True,
            "trained_branch_population": {"state_hash": "b"},
            "trained_root_colonies": {"state_hash": "r"},
            "lifecycle_runtime_states": {"state_hash": "l"},
            "nutrient_toxic_runtime_memory": {"memory_hash": "n"},
        },
        tmp_path / "state",
    )
    result = run_cross_process_runtime_reload_eval(tmp_path / "state", "datasets/v0_8_5_boundary_aware", tmp_path, mode="quick")
    assert result["used_new_process"] is True
    assert result["forbidden_field_access_count"] == 0
