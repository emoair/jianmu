from jianmu.self_learning.darwinforge.dataset_redqueen_scheduler import build_redqueen_dataset_schedule


def test_dataset_redqueen_scheduler_keeps_boundary_minimum(tmp_path) -> None:
    result = build_redqueen_dataset_schedule(tmp_path)
    assert result["redqueen_dataset_scheduler_passed"] is True
    assert result["category_weights"]["unsupported boundary negative"] >= 0.05
