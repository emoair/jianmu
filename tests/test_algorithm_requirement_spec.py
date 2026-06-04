from jianmu.self_learning.darwinforge.algorithm_requirement_spec import AlgorithmRequirementSpec, AlgorithmVariantConfig, build_requirement_spec
from jianmu.self_learning.darwinforge.algorithm_semantic_skeleton import build_semantic_skeleton


def test_algorithm_requirement_spec_contains_mutation_policies():
    spec = build_requirement_spec(build_semantic_skeleton(0), 5, "train")
    assert isinstance(spec, AlgorithmRequirementSpec)
    assert spec.variable_renaming_policy
    assert spec.helper_function_policy == "split_helper"
    assert AlgorithmVariantConfig.for_scale("large").total_variant_target == 256_000
