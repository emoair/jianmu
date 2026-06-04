from pathlib import Path

from jianmu.self_learning.darwinforge.archive_index_builder import build_active_core_manifest, build_active_frontier_manifest, build_legacy_experiment_manifest, build_readme_cleanup_report


def test_active_core_manifest_generated(tmp_path: Path) -> None:
    payload = build_active_core_manifest(Path.cwd(), tmp_path)
    assert payload["active_core_modules"]
    assert payload["active_core_entrypoints"]
    assert payload["active_core_tests"]


def test_active_frontier_manifest_generated(tmp_path: Path) -> None:
    payload = build_active_frontier_manifest(Path.cwd(), tmp_path)
    assert "function_frontier" in payload["active_frontier_modules"]
    assert payload["production_supported"]["function"] is False
    assert payload["production_supported"]["recursion"] is False


def test_legacy_experiment_manifest_generated(tmp_path: Path) -> None:
    payload = build_legacy_experiment_manifest(Path.cwd(), tmp_path)
    assert payload["legacy_experiment_modules"]
    assert payload["safe_to_keep"] is True
    assert payload["not_safe_to_move_yet"]


def test_readme_links_baseline_and_archive(tmp_path: Path) -> None:
    payload = build_readme_cleanup_report(Path.cwd(), tmp_path)
    assert payload["links_baseline"] is True
    assert payload["links_archive"] is True
    assert payload["no_production_claim_added"] is True
