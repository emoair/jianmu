from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.runtime_state_capture import RuntimeStateCapture, RuntimeStateCaptureConfig


def test_runtime_state_capture_hooks_do_not_change_training_output(tmp_path):
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=42)
    before = population.summary()
    capture = RuntimeStateCapture(RuntimeStateCaptureConfig(output_dir=str(tmp_path)))
    capture.on_training_start({"seed": 42})
    capture.on_branch_population_update(population)
    after = population.summary()
    assert before == after


def test_runtime_state_capture_export_marks_missing(tmp_path):
    capture = RuntimeStateCapture(RuntimeStateCaptureConfig(output_dir=str(tmp_path)))
    result = capture.export_full_runtime_state()
    assert result["runtime_capture_passed"] is False
    assert "trained_branch_population" in result["missing_capture_components"]
