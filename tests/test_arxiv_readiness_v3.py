from jianmu.self_learning.darwinforge.arxiv_readiness_v3 import assess_arxiv_readiness_v3


def test_arxiv_readiness_v3_requires_figures_and_full_state():
    result = assess_arxiv_readiness_v3(
        {"persisted_state_support_level": "partial"},
        {"runtime_full_state_consistency_passed": True},
        {"cross_process_reload_passed": True},
        {"overall_ood_false_accept_rate": 0.0, "current_supported_retention_rate": 1.0},
        {"stable_across_seeds": True},
        {"forbidden_field_in_state_count": 0},
        True,
        True,
    )
    assert result["ready_for_arxiv_technical_report"] is False


def test_arxiv_readiness_v3_preserves_non_claims():
    result = assess_arxiv_readiness_v3({}, {}, {}, {}, {}, {}, False, False)
    assert "solved OOD" in result["required_non_claims"]
