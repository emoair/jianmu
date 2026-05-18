import pytest

from jianmu.sandbox import SandboxResult, has_supported_c_compiler
from jianmu.self_learning.ir_tokens import IRToken, expected_binary_add_tokens, tokens_to_c_code
from jianmu.self_learning.prefix_dataset import PrefixTrainingTask, build_tiny_prefix_dataset
from jianmu.self_learning.prefix_evolution import PrefixEvolutionTrainer, build_initial_population
from jianmu.self_learning.prefix_neuron import PrefixNeuron
from jianmu.self_learning.prefix_state import PrefixState


def test_tiny_prefix_dataset_reproducible():
    first = build_tiny_prefix_dataset()
    second = build_tiny_prefix_dataset()
    assert first == second
    assert len(first) == 6
    for task in first:
        assert task.input_text
        assert task.target_tokens
        assert task.expected_output.endswith("\n")


def test_ir_tokens_convert_to_c_and_run():
    if not has_supported_c_compiler():
        pytest.skip("gcc/clang/cl not found")
    code = tokens_to_c_code(expected_binary_add_tokens(1, 2))
    assert "printf" in code
    result = __import__("jianmu.sandbox", fromlist=["Sandbox"]).Sandbox().run(code)
    assert result.compile_success, result.stderr or result.stdout
    assert result.run_success, result.stderr or result.stdout
    assert result.stdout == "3\n"


def test_prefix_neuron_proposal_is_deterministic():
    state = PrefixState("写一个 C 程序输出 1+2", [], 0)
    neuron = PrefixNeuron("n", "start_include", "INCLUDE_STDIO", "none", 30)
    assert neuron.propose(state) == neuron.propose(state)


def test_prefix_evolution_updates_scores():
    tasks = build_tiny_prefix_dataset()[:2]
    population = build_initial_population(population_size=16, seed=7)
    before = [neuron.score for neuron in population]
    trainer = PrefixEvolutionTrainer(tasks, population, generations=2, seed=7)
    trainer.train()
    after = [neuron.score for neuron in population]
    assert before != after


def test_prefix_evolution_report_has_metrics():
    tasks = build_tiny_prefix_dataset()[:2]
    population = build_initial_population(population_size=7, seed=42)
    report = PrefixEvolutionTrainer(tasks, population, generations=3, seed=42).train()
    assert report.generation_count == 3
    assert len(report.best_sequence_accuracy_by_generation) == 3
    assert len(report.full_sequence_success_by_generation) == 3
    assert len(report.compile_success_by_generation) == 3
    assert len(report.task_success_by_generation) == 3
    assert report.best_neurons
    assert report.final_population_summary


def test_no_generated_output_self_certification():
    class FakeSandbox:
        def run(self, source_code):
            return SandboxResult(
                compiler="fake",
                compile_success=True,
                run_success=True,
                stdout="999\n",
                stderr="",
                returncode=0,
                error_type="",
                command="fake",
            )

    task = PrefixTrainingTask(
        task_id="self_cert_guard",
        input_text="写一个 C 程序输出 1+2",
        target_tokens=expected_binary_add_tokens(1, 2),
        expected_output="3\n",
    )
    population = build_initial_population(population_size=7, seed=42)
    trainer = PrefixEvolutionTrainer([task], population, generations=1, seed=42)
    trainer.sandbox = FakeSandbox()
    report = trainer.train()
    assert report.compile_success_by_generation[0] == 1.0
    assert report.task_success_by_generation[0] == 0.0


def test_existing_v05_imports_still_available():
    from jianmu.hierarchical_router import HierarchicalSemanticRouter
    from jianmu.runtime import Runtime

    assert HierarchicalSemanticRouter()
    assert Runtime()
