import pytest

from jianmu.hierarchical_router import HierarchicalSemanticRouter
from jianmu.ir import ProgramIR, SumExpression, Variable
from jianmu.routes import RouteCandidate
from jianmu.runtime import Runtime
from jianmu.sandbox import has_supported_c_compiler
from jianmu.candidate_executor import CandidateExecutor
from jianmu.trace_cache import TraceCache


HAS_COMPILER = has_supported_c_compiler()


def make_two_sum_ir():
    return ProgramIR(
        variables=[Variable("a", value=1), Variable("b", value=1)],
        expression=SumExpression(operands=["a", "b"]),
    )


@pytest.fixture
def router():
    return HierarchicalSemanticRouter()


@pytest.fixture
def rt(tmp_path):
    r = Runtime()
    r._cache._path = str(tmp_path / "trace_cache.json")
    r._memory._path = str(tmp_path / "route_memory.json")
    return r


def test_neuron_detects_negation_before_addition(router):
    features = router.analyze("不要多加2，保持不变", make_two_sum_ir())
    assert features.negated is True
    assert features.edit_intent_scores["KeepExistingNeuron"] > features.edit_intent_scores["AppendOperandNeuron"]


def test_neuron_distinguishes_append_from_replace(router):
    features = router.analyze("把最后一个1改成2", make_two_sum_ir())
    assert features.edit_intent_scores["ReplaceOperandNeuron"] > features.edit_intent_scores["AppendOperandNeuron"]
    candidates = router.generate_candidates(features, make_two_sum_ir())
    assert candidates[0].route_id == "replace_last_operand"


def test_append_multiple_operands(rt):
    result = rt.run("再加两个2", previous_ir=make_two_sum_ir(), speculative=True)
    assert result.selected_candidate.candidate.route_id == "append_multiple_literals_to_existing_sum"
    assert result.selected_candidate.candidate.intent["new_value"] == 2
    assert result.selected_candidate.candidate.intent["append_count"] == 2
    if HAS_COMPILER:
        assert result.sandbox_result.stdout.strip() == "6"


def test_explicit_expression_rewrite(rt):
    result = rt.run("从1+1变成1+1+2", speculative=True)
    assert result.selected_candidate.candidate.route_id == "explicit_expression_rewrite"
    assert result.selected_candidate.candidate.intent["values"] == [1, 1, 2]
    if HAS_COMPILER:
        assert result.sandbox_result.stdout.strip() == "4"


def test_chinese_number_value_extraction(router):
    features = router.analyze("再加一个二", make_two_sum_ir())
    assert features.extracted_numbers == [2]
    candidates = router.generate_candidates(features, make_two_sum_ir())
    append = next(c for c in candidates if c.route_id == "append_literal_to_existing_sum")
    assert append.intent["new_value"] == 2


def test_negative_number_extraction(router):
    features = router.analyze("再加一个-2", make_two_sum_ir())
    assert features.unsupported_expression is False
    assert features.extracted_numbers == [-2]
    candidates = router.generate_candidates(features, make_two_sum_ir())
    append = next(c for c in candidates if c.route_id == "append_literal_to_existing_sum")
    assert append.intent["new_value"] == -2


def test_punctuation_number_list_extraction(router):
    features = router.analyze("三个整数 1、2、3 并输出和")
    assert features.extracted_numbers == [1, 2, 3]
    candidates = router.generate_candidates(features)
    generate = next(c for c in candidates if c.route_id == "generate_new_sum_from_text")
    assert generate.intent["values"] == [1, 2, 3]
    assert generate.expected_output == "6\n"


def test_pure_english_natural_language_returns_unsupported(router):
    features = router.analyze("sum of three numbers")
    assert features.unsupported_language is True
    candidates = router.generate_candidates(features)
    assert candidates[0].route_id == "unsupported_language_input"
    assert candidates[0].intent["action"] == "unsupported_input"


def _assert_unsupported_expression_result(result, rt):
    assert result.selected_candidate is not None
    assert result.selected_candidate.candidate.route_id == "unsupported_expression_input"
    assert result.selected_candidate.success is False
    assert result.generated_code == ""
    assert result.program_ir == {}
    assert result.sandbox_result.compile_success is False
    assert result.sandbox_result.run_success is False
    assert TraceCache(rt._cache._path)._load() == {}


def test_subtraction_expression_is_unsupported_in_v05(rt):
    result = rt.run("输出1-2", speculative=True)
    _assert_unsupported_expression_result(result, rt)


def test_multiplication_expression_is_unsupported_in_v05(rt):
    result = rt.run("输出1*2", speculative=True)
    _assert_unsupported_expression_result(result, rt)


def test_division_expression_is_unsupported_in_v05(rt):
    result = rt.run("输出1/2", speculative=True)
    _assert_unsupported_expression_result(result, rt)


def test_negation_detector_does_not_trigger_on_fenbie(rt):
    text = "定义三个 int，分别是 1、2、3，然后 printf 输出和"
    features = HierarchicalSemanticRouter().analyze(text)
    assert features.negated is False

    result = rt.run(text, speculative=True)
    assert result.semantic_features.negated is False
    if not HAS_COMPILER:
        pytest.skip("gcc/clang/cl not found")
    assert result.sandbox_result.stdout.strip() == "6"
    assert result.selected_candidate.success is True


@pytest.mark.parametrize("text", ["分别输出 1、2、3 的和", "fenbie"])
def test_negation_detector_ignores_non_negation_tokens(text):
    features = HierarchicalSemanticRouter().analyze(text)
    assert features.negated is False


@pytest.mark.parametrize("text", ["不要多加2，保持不变", "not change the current program", "非追加"])
def test_negation_detector_still_detects_real_negation(text):
    features = HierarchicalSemanticRouter().analyze(text, make_two_sum_ir())
    assert features.negated is True


def test_expected_output_provenance_present_on_candidates(router):
    ir = make_two_sum_ir()
    cases = [
        ("再加一个2", ir),
        ("再加两个2", ir),
        ("把最后一个1改成2", ir),
        ("不要多加2，保持不变", ir),
        ("从1+1变成1+1+2", None),
        ("定义三个 int，分别是 1、2、3，然后 printf 输出和", None),
        ("sum of three numbers", None),
    ]
    for text, previous_ir in cases:
        features = router.analyze(text, previous_ir)
        candidates = router.generate_candidates(features, previous_ir)
        assert candidates
        for candidate in candidates:
            assert candidate.expected_output_provenance in {
                "external",
                "explicit_expression",
                "previous_ir_append",
                "previous_ir_replace",
                "previous_ir_noop",
                "generated_values",
                "none",
            }


def test_no_self_certification_when_provenance_none():
    if not HAS_COMPILER:
        pytest.skip("gcc/clang/cl not found")
    candidate = RouteCandidate(
        route_id="untrusted_generated_values",
        source="test",
        intent={"action": "generate_sum_program", "var_count": 2, "values": [1, 1]},
        expert_plan=["IncludeExpert", "VariableDefinitionExpert", "SumExpressionExpert",
                     "PrintfExpert", "MainFunctionExpert", "ConsistencyCheckExpert"],
        prior_score=1.0,
        expected_output="2\n",
        expected_output_provenance="none",
    )
    result = CandidateExecutor().execute(candidate)
    assert result.score_report.compile_success == 1
    assert result.score_report.run_success == 1
    assert result.score_report.expected_output_match == 0
    assert result.score_report.correctness_score < 1.0
    assert result.success is False


def test_no_op_wins_for_negated_append(rt):
    result = rt.run("不要多加2，保持不变", previous_ir=make_two_sum_ir(), speculative=True)
    assert result.selected_candidate.candidate.route_id == "no_op_keep_existing"
    if HAS_COMPILER:
        assert result.sandbox_result.stdout.strip() == "2"


def test_replace_wins_over_append_when_semantics_say_replace(rt):
    result = rt.run("把最后一个1改成2", previous_ir=make_two_sum_ir(), speculative=True)
    assert result.selected_candidate.candidate.route_id == "replace_last_operand"
    append = next(c for c in result.all_candidates if c.route_id == "append_literal_to_existing_sum")
    replace = next(c for c in result.all_candidates if c.route_id == "replace_last_operand")
    assert replace.semantic_match_score > append.semantic_match_score
    if HAS_COMPILER:
        assert result.sandbox_result.stdout.strip() == "3"


def test_hierarchical_router_returns_audit_features(rt):
    result = rt.run("再加一个2", previous_ir=make_two_sum_ir(), speculative=True)
    assert result.semantic_features is not None
    assert result.neuron_results is not None
    assert any(n.neuron_name == "AppendOperandNeuron" for n in result.neuron_results)
    assert result.selected_candidate is not None
    assert result.selected_candidate.semantic_match_score == result.selected_candidate.candidate.semantic_match_score
    assert result.rejected_candidates is not None
