from pathlib import Path

from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.darwinforge.ood_guard_balancing import apply_ood_guard_balancing
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


def test_ood_guard_balancing_reduces_false_accept():
    samples = [
        {"sample_id": "ood-en", "input_mode": "ood_english", "supported": False, "unsupported_reason": "unsupported_language"},
        {"sample_id": "bad-div", "input_mode": "unsupported_arithmetic", "supported": False, "unsupported_reason": "division_by_zero"},
        {"sample_id": "ok", "input_mode": "arabic_math_expression", "supported": True, "semantic_domain": "arithmetic"},
    ]
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=42)

    metrics = apply_ood_guard_balancing(population, samples, before_metrics={"ood_false_accept_rate": 0.33, "ood_rejection_rate": 0.67})

    assert metrics["ood_false_accept_after"] <= metrics["ood_false_accept_before"]
    assert metrics["ood_guard_seed_count"] > 0


def test_arithmetic_supported_retention_rate_reported():
    samples = [{"sample_id": "ok", "input_mode": "arabic_math_expression", "supported": True, "semantic_domain": "arithmetic"}]

    metrics = apply_ood_guard_balancing(LayerPreservedPopulation.initialize(population_per_layer=8, seed=43), samples)

    assert metrics["arithmetic_supported_retention_rate"] == 1.0


def test_surface_features_include_unsupported_arithmetic_signals():
    features = extract_surface_features("5/0")

    assert features["division_by_zero_signal"] is True
    assert features["unsupported_arithmetic_signal"] is True


def test_no_external_api_calls():
    source = Path("jianmu/self_learning/darwinforge/ood_guard_balancing.py").read_text(encoding="utf-8")

    assert "requests" not in source
    assert "openai" not in source
    assert "httpx" not in source
