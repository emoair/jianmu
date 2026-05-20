from pathlib import Path

from jianmu.self_learning.darwinforge.beam_backtracking import WideBeamBacktrackingConfig, WideBeamBacktrackingSearch
from jianmu.self_learning.darwinforge.canonicalized_training_eval import build_training_features
from jianmu.self_learning.darwinforge.layer_clone import LayerCloneConfig, clone_layer_population
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


def test_wide_beam_generates_multiple_complete_paths():
    population = LayerPreservedPopulation.initialize(population_per_layer=16, seed=11)
    search = WideBeamBacktrackingSearch(WideBeamBacktrackingConfig(beam_size=12, proposals_per_layer=4, max_complete_paths=20, seed=11))
    features = build_training_features("1+2", canonicalization_enabled=True)

    genomes = search.generate_paths(population, features, generation=0)

    assert len(genomes) > 1
    assert any(not genome.branch_path.early_exit for genome in genomes)


def test_wide_beam_respects_max_complete_paths():
    population = LayerPreservedPopulation.initialize(population_per_layer=24, seed=12)
    search = WideBeamBacktrackingSearch(
        WideBeamBacktrackingConfig(beam_size=32, proposals_per_layer=8, max_complete_paths=5, stochastic_samples_per_layer=4, seed=12)
    )

    genomes = search.generate_paths(population, build_training_features("1+2*3", True), generation=0)

    assert len(genomes) <= 5


def test_early_exit_paths_do_not_dominate_beam():
    population = LayerPreservedPopulation.initialize(population_per_layer=16, seed=13)
    for neuron in population.per_layer["language_target"]:
        if neuron.option == "reject_unsupported_language":
            neuron.weights["has_english_sentence"] = 100
            neuron.threshold = 0
    search = WideBeamBacktrackingSearch(WideBeamBacktrackingConfig(beam_size=16, proposals_per_layer=6, max_complete_paths=16, seed=13))

    genomes = search.generate_paths(population, build_training_features("calculate one plus two", True), generation=0)
    early_count = sum(1 for genome in genomes if genome.branch_path.early_exit)

    assert early_count <= max(1, search.config.beam_size // 4)


def test_backtracking_creates_layer_clones():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=14)
    clones = clone_layer_population(
        population.per_layer["arithmetic_family"],
        "arithmetic_family",
        LayerCloneConfig(clone_count_per_layer=3, perturbation_scale=0.1, seed=14),
        generation=2,
    )
    search = WideBeamBacktrackingSearch(WideBeamBacktrackingConfig(beam_size=16, proposals_per_layer=4, max_complete_paths=20, seed=14))

    genomes = search.generate_paths(
        population,
        build_training_features("1+2", True),
        active_clones={"arithmetic_family": clones},
        generation=2,
    )

    source_ids = {
        decision.evidence.get("source_clone_id")
        for genome in genomes
        for decision in genome.branch_path.decisions
        if decision.layer_name == "arithmetic_family"
    }
    assert any(source_id and source_id != "base" for source_id in source_ids)


def test_no_expression_oracle_import_in_beam_backtracking():
    source = Path("jianmu/self_learning/darwinforge/beam_backtracking.py").read_text(encoding="utf-8")

    assert "expression_oracle" not in source
    assert "parse_controlled_expression" not in source


def test_no_flat_classifier_imports():
    for path in Path("jianmu/self_learning/darwinforge").glob("*beam*.py"):
        source = path.read_text(encoding="utf-8")
        assert "learned_router.perceptron" not in source
        assert "arithmetic_targetir.hashed_perceptron" not in source


def test_candidate_generation_does_not_use_targetir_or_target_branch_path():
    source = Path("jianmu/self_learning/darwinforge/beam_backtracking.py").read_text(encoding="utf-8")

    assert "target_ir" not in source
    assert "expected_output" not in source
    assert "target_branch_path" not in source


def test_no_external_api_calls():
    for path in [
        Path("jianmu/self_learning/darwinforge/beam_backtracking.py"),
        Path("jianmu/self_learning/darwinforge/layer_clone.py"),
        Path("jianmu/self_learning/darwinforge/wide_beam_backtracking_trainer.py"),
    ]:
        source = path.read_text(encoding="utf-8")
        assert "requests" not in source
        assert "openai" not in source
        assert "httpx" not in source
