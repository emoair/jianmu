from pathlib import Path

from jianmu.self_learning.darwinforge.ood_candidate_datasets import write_ood_candidate_datasets


def test_ood_candidate_datasets_do_not_modify_original_dataset(tmp_path):
    original = tmp_path / "datasets" / "v0_7_0"
    original.mkdir(parents=True)
    marker = original / "marker.txt"
    marker.write_text("unchanged", encoding="utf-8")
    out = tmp_path / "datasets" / "v0_8_4_ood_boundary_candidates"
    write_ood_candidate_datasets(
        [{"boundary_label": "true_false_accept", "sample_id": "s1", "raw_text": "poem", "canonical_text": "poem"}],
        out,
    )
    assert marker.read_text(encoding="utf-8") == "unchanged"


def test_ood_candidate_dataset_manifest_exists(tmp_path):
    manifest = write_ood_candidate_datasets(
        [{"boundary_label": "near_ood_generalization_candidate", "sample_id": "s1", "raw_text": "算三加四", "canonical_text": "3+4"}],
        tmp_path,
    )
    assert Path(manifest["manifest_path"]).exists()
    assert manifest["auto_added_to_training"] is False
