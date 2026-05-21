import json

from jianmu.self_learning.darwinforge.persisted_router_state import load_persisted_router_state, save_persisted_router_state


def test_persisted_state_manifest_created(tmp_path):
    source = tmp_path / "records"
    source.mkdir()
    (source / "freebeam_boundary_metrics.json").write_text(json.dumps({"metrics": {"x": 1}}), encoding="utf-8")
    (source / "boundary_generalization_metrics.json").write_text(json.dumps({"overall_ood_false_accept_rate": 0.0}), encoding="utf-8")
    (source / "no_label_inference_guard.json").write_text(json.dumps({"no_label_inference_passed": True}), encoding="utf-8")
    result = save_persisted_router_state(source, tmp_path / "state")
    assert result["state_saved"] is True
    assert (tmp_path / "state" / "state_manifest.json").exists()


def test_persisted_state_excludes_forbidden_fields(tmp_path):
    source = tmp_path / "records"
    source.mkdir()
    (source / "freebeam_boundary_metrics.json").write_text(json.dumps({"target_ir": "secret", "ok": 1}), encoding="utf-8")
    (source / "boundary_generalization_metrics.json").write_text(json.dumps({"boundary_label": "hard_ood"}), encoding="utf-8")
    (source / "no_label_inference_guard.json").write_text(json.dumps({"expected_output": 7}), encoding="utf-8")
    result = save_persisted_router_state(source, tmp_path / "state")
    assert result["forbidden_field_in_state_count"] == 0


def test_persisted_state_load_roundtrip(tmp_path):
    source = tmp_path / "records"
    source.mkdir()
    for name in ["freebeam_boundary_metrics.json", "boundary_generalization_metrics.json", "no_label_inference_guard.json"]:
        (source / name).write_text("{}", encoding="utf-8")
    save_persisted_router_state(source, tmp_path / "state")
    loaded = load_persisted_router_state(tmp_path / "state")
    assert loaded["state_loaded"] is True
    assert loaded["checksum_matches_manifest"] is True
