from jianmu.self_learning.branchchain.branch_types import BranchPath
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.candidate import CandidateGenome


def _genome(policy):
    return CandidateGenome("g", BranchPath(), [], "", policy)


def test_atomic_synthesis_accepts_function_policy():
    p = AtomicSynthesis().synthesize(_genome("canonical_function_targetir"), {"signed_numbers": [7]})
    assert p.c_program and "static int calc" in p.c_program
    assert "production_supported=false" in p.target_ir_canonical


def test_atomic_synthesis_accepts_array_policy():
    p = AtomicSynthesis().synthesize(_genome("canonical_array_targetir"), {"signed_numbers": [7]})
    assert p.c_program and "int a[4]" in p.c_program


def test_atomic_synthesis_accepts_function_array_policy():
    p = AtomicSynthesis().synthesize(_genome("canonical_function_array_targetir"), {"signed_numbers": [7]})
    assert p.c_program and "sum3" in p.c_program


def test_atomic_synthesis_accepts_recursion_policy():
    p = AtomicSynthesis().synthesize(_genome("canonical_structured_recursion_targetir"), {"signed_numbers": [5]})
    assert p.c_program and "fact" in p.c_program
    assert "recursion_mode=bounded_structural_recursion_validation" in p.target_ir_canonical


def test_atomic_synthesis_rejects_unknown_policy():
    p = AtomicSynthesis().synthesize(_genome("canonical_unknown_targetir"), {"signed_numbers": [7]})
    assert p.failure_reason == "unsupported_target_builder"

