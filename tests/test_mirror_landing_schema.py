from jianmu.self_learning.darwinforge.mirror_landing_schema import MIRROR_TERMS, MirrorRuntimeProbeConfig


def test_mirror_landing_schema_terms_and_defaults() -> None:
    assert "mirror_disagreement" in MIRROR_TERMS
    cfg = MirrorRuntimeProbeConfig()
    assert cfg.events == 30000
    assert cfg.explicit_opt_in_required is True

