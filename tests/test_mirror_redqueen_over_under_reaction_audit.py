from jianmu.self_learning.darwinforge.mirror_redqueen_over_under_reaction_audit import audit_over_under_reaction


def test_over_under_reaction_audit_blocks_ignored_disagreement(tmp_path) -> None:
    cycles = [{"mirror": {"mirror_disagreement_rate": 0.1}, "redqueen": {"redqueen_adjustment_events_from_mirror": 0}}]
    result = audit_over_under_reaction(tmp_path, cycles)
    assert result["over_under_reaction_audit_passed"] is False
    assert result["mirror_disagreement_ignored"] is True

