from jianmu.self_learning.darwinforge.runtime_full_state_builder import build_runtime_full_state, scan_forbidden_fields


def _capture():
    return {
        "runtime_capture_passed": True,
        "trained_branch_population": {"state_hash": "b"},
        "trained_root_colonies": {"state_hash": "r"},
        "lifecycle_runtime_states": {"state_hash": "l"},
        "nutrient_toxic_runtime_memory": {"memory_hash": "n"},
    }


def test_runtime_full_state_builder_requires_all_core_components(tmp_path):
    result = build_runtime_full_state(_capture(), tmp_path)
    assert result["persisted_state_support_level"] == "full_router_root"
    partial = _capture()
    partial["trained_root_colonies"] = None
    assert build_runtime_full_state(partial, tmp_path / "partial")["persisted_state_support_level"] == "partial"


def test_runtime_full_state_forbidden_field_scan():
    scan = scan_forbidden_fields({"nested": {"target_ir": "forbidden"}})
    assert scan["forbidden_field_in_state_count"] == 1
