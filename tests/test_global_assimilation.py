from jianmu.self_learning.darwinforge.global_assimilation import apply_global_assimilation, extract_assimilation_records
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


def _subbeam(sample_id="train-a", exact=True):
    return {
        "sample_id": sample_id,
        "correct_targetir_in_subbeam": exact,
        "subbeam_best_exact": exact,
        "subbeam_best_targetir": "add(lit(1),lit(2))",
        "first_success_rank": 2,
        "fork_layer": "slot_binding_policy",
        "fork_reason": "first_low_score_correct_layer",
        "generated_paths_summary": [
            {"target_ir_pred": "add(lit(1),lit(2))", "decisions": [["slot_binding_policy", "surface_number_order"]]},
        ],
    }


def test_global_assimilation_extracts_train_only_records():
    samples = [{"sample_id": "train-a", "split": "train", "input_text": "1+2", "number_count": 2, "operator_count": 1}]

    records = extract_assimilation_records([_subbeam()], [], samples)

    assert len(records) == 1
    assert records[0].split == "train"
    assert records[0].assimilation_updates


def test_global_assimilation_skips_eval_and_ood():
    samples = [
        {"sample_id": "eval-a", "split": "eval", "input_text": "1+2"},
        {"sample_id": "ood-a", "split": "ood", "input_text": "poem"},
    ]

    records = extract_assimilation_records([_subbeam("eval-a"), _subbeam("ood-a")], [], samples)

    assert all(not record.rescued_by_subbeam for record in records)


def test_global_assimilation_updates_branch_neurons():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=42)
    samples = [{"sample_id": "train-a", "split": "train", "input_text": "1+2", "number_count": 2, "operator_count": 1}]
    records = extract_assimilation_records([_subbeam()], [], samples)

    metrics = apply_global_assimilation(population, records)

    assert metrics["assimilation_record_count"] == 1
    assert metrics["branch_neuron_updated_count"] > 0
    assert "slot_binding_policy" in metrics["updated_layer_distribution"]
