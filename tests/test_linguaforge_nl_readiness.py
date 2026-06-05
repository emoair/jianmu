import inspect
from pathlib import Path

from jianmu.self_learning.darwinforge import linguaforge_nl_alpha_core as core


def test_readiness_requires_no_nl_bypass():
    row = core.build_row(0, 188)
    token = core.nl_to_token_metrics([row]) | core.token_audit([row])
    assert token["nl_bypassed_token_layer_count"] == 0


def test_readiness_keeps_natural_language_layer_completed_false():
    assert "natural_language_layer_completed" in inspect.getsource(core.readiness)
    assert "production_nl_interface" in inspect.getsource(core.readiness)


def test_readiness_ready_for_official_release_false():
    assert "ready_for_official_release" in inspect.getsource(core.readiness)
    assert "False" in inspect.getsource(core.readiness)


def test_no_expression_oracle_import():
    assert "expression_oracle" not in str(core.__dict__)


def test_no_external_api_calls():
    text = Path(core.__file__).read_text(encoding="utf-8")
    assert "requests." not in text
    assert "urllib" not in text
    assert "openai" not in text.lower()


def test_no_hardcoded_keyword_gate():
    text = Path(core.__file__).read_text(encoding="utf-8").lower()
    assert "keyword rejection" not in text


def test_real_promotion_disabled():
    text = Path(core.__file__).read_text(encoding="utf-8")
    assert "real_promotion_enabled = True" not in text
