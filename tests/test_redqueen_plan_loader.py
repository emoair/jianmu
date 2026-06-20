import json

from jianmu.self_learning.darwinforge.redqueen_plan_loader import load_redqueen_iteration_plan


def _write_sources(root, frozen=True):
    root.mkdir()
    plan = {
        "next_plan_generated": True,
        "category_weights": {"function": 1.0},
        "difficulty_levels": {"function": 2},
        "active_review_allocations": {"function": 1.0},
        "shape_diversity_targets": {"function": False},
        "boundary_recheck_targets": {"default_blocking": 1, "unsupported_boundary": 1},
        "rollback_recheck_targets": {"rollback": 1},
        "replay_recheck_targets": {"mixed": 1},
        "promotion_frozen": frozen,
        "default_profile_unchanged_required": True,
        "real_promotion_forbidden": True,
        "production_claim_forbidden": True,
    }
    for name, payload in {
        "redqueen_next_validation_plan.json": plan,
        "redqueen_metrics_snapshot.json": {"categories": []},
        "redqueen_active_review_allocation.json": {},
        "redqueen_difficulty_schedule.json": {},
        "redqueen_self_governance_policy.json": {},
    }.items():
        (root / name).write_text(json.dumps(payload), encoding="utf-8")


def test_redqueen_plan_loader_requires_v1_0_8_2_plan(tmp_path):
    src = tmp_path / "src"
    _write_sources(src)
    result = load_redqueen_iteration_plan(src, tmp_path / "out")
    assert result["source_plan_loaded"] is True
    assert result["plan_loader_passed"] is True


def test_redqueen_plan_loader_requires_promotion_frozen(tmp_path):
    src = tmp_path / "src"
    _write_sources(src, frozen=False)
    result = load_redqueen_iteration_plan(src, tmp_path / "out")
    assert result["promotion_frozen"] is False
    assert result["plan_loader_passed"] is False
