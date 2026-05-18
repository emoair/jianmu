import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jianmu.runtime import Runtime
from jianmu.ir import ProgramIR, Variable, SumExpression
from jianmu.speculative_router import SpeculativeRouter
from jianmu.route_memory import RouteMemory
from jianmu.trace_cache import TraceCache
from jianmu.sandbox import has_supported_c_compiler

HAS_COMPILER = has_supported_c_compiler()
needs_compiler = pytest.mark.skipif(not HAS_COMPILER, reason="gcc/clang/cl not found")


def make_two_sum_ir():
    return ProgramIR(
        variables=[Variable("a", value=1), Variable("b", value=1)],
        expression=SumExpression(operands=["a", "b"]),
    )


@pytest.fixture
def rt(tmp_path):
    r = Runtime()
    r._cache._path = str(tmp_path / "trace_cache.json")
    r._memory._path = str(tmp_path / "route_memory.json")
    return r


@pytest.fixture
def spec_router():
    return SpeculativeRouter()


# ── 1. 多候选生成 ─────────────────────────────────────────────────────────────
def test_router_generates_multiple_candidates_for_ambiguous_append(spec_router):
    ir = make_two_sum_ir()
    candidates = spec_router.generate_candidates("让程序多加一个 2", previous_ir=ir)
    route_ids = [c.route_id for c in candidates]
    assert "append_literal_to_existing_sum" in route_ids
    assert "generate_new_sum_from_text" in route_ids
    assert "replace_last_operand" in route_ids
    assert len(candidates) >= 3


# ── 2. 投机执行选择正确路径 ───────────────────────────────────────────────────
@needs_compiler
def test_speculative_execution_selects_correct_append_route(rt):
    ir = make_two_sum_ir()
    result = rt.run("让程序多加一个 2", previous_ir=ir,
                    expected_output="4\n", speculative=True)
    assert result.selected_candidate is not None
    assert result.selected_candidate.candidate.route_id == "append_literal_to_existing_sum"
    assert result.sandbox_result.stdout.strip() == "4"


# ── 3. 失败候选被记录到 RouteMemory ──────────────────────────────────────────
@needs_compiler
def test_failed_candidates_are_recorded(rt):
    ir = make_two_sum_ir()
    rt.run("让程序多加一个 2", previous_ir=ir,
           expected_output="4\n", speculative=True)
    data = RouteMemory(rt._memory._path)._load()
    # At least one key exists
    assert len(data) >= 1
    # Winner has success_count >= 1
    all_entries = [entry for key in data for entry in data[key].values()]
    assert any(e["success_count"] >= 1 for e in all_entries)
    # At least one loser has failure_count >= 1
    assert any(e["failure_count"] >= 1 for e in all_entries)


# ── 4. RouteMemory 提升成功路径的 prior_score ─────────────────────────────────
@needs_compiler
def test_route_memory_increases_prior_for_successful_route(rt):
    ir = make_two_sum_ir()
    # First run — establishes memory
    rt.run("让程序多加一个 2", previous_ir=ir,
           expected_output="4\n", speculative=True)

    # Second run — prior_score of winner should be boosted
    ir2 = make_two_sum_ir()
    candidates_before_boost = SpeculativeRouter().generate_candidates("再加一个 3", previous_ir=ir2)
    default_prior = next(c.prior_score for c in candidates_before_boost
                         if c.route_id == "append_literal_to_existing_sum")

    boost = rt._memory.get_prior_boost("再加一个 3", True, "append_literal_to_existing_sum")
    assert boost > 0, "Expected positive prior boost after successful run"
    assert default_prior + boost > default_prior


# ── 5. speculative=True 不允许单候选捷径 ─────────────────────────────────────
@needs_compiler
def test_no_single_intent_shortcut(rt):
    ir = make_two_sum_ir()
    result = rt.run("让程序多加一个 2", previous_ir=ir,
                    expected_output="4\n", speculative=True)
    assert result.executed_candidates is not None
    assert len(result.executed_candidates) >= 2


# ── 6. 失败候选不写入 TraceCache ──────────────────────────────────────────────
@needs_compiler
def test_no_cache_write_for_losing_candidates(rt):
    ir = make_two_sum_ir()
    result = rt.run("让程序多加一个 2", previous_ir=ir,
                    expected_output="4\n", speculative=True)
    cache = TraceCache(rt._cache._path)
    # Only winner's intent should be in cache
    losers = result.rejected_candidates or []
    for loser in losers:
        if not loser.success:
            cached = cache.get(loser.candidate.intent,
                               ir.to_dict() if loser.candidate.requires_previous_ir else None)
            assert cached is None, f"Loser {loser.candidate.route_id} was incorrectly cached"


# ── 7. previous_ir=None 时 append 路径不能成功 ────────────────────────────────
@needs_compiler
def test_previous_ir_required_for_append_route(rt):
    result = rt.run("让程序多加一个 2", previous_ir=None,
                    speculative=True)
    # append_literal_to_existing_sum must not be the winner when no previous_ir
    if result.selected_candidate:
        winner_id = result.selected_candidate.candidate.route_id
        assert winner_id != "append_literal_to_existing_sum" or not result.selected_candidate.success


# ── 8. RouteMemory 与 TraceCache 文件分离 ────────────────────────────────────
def test_route_memory_is_not_trace_cache(rt):
    assert rt._memory._path != rt._cache._path
    # Semantic check: RouteMemory stores route_id experience, TraceCache stores code
    # Just verify they are different files
    assert os.path.basename(rt._memory._path) != os.path.basename(rt._cache._path)


# ── 9. 候选生成确定性 ─────────────────────────────────────────────────────────
def test_deterministic_candidate_generation(spec_router):
    ir = make_two_sum_ir()
    c1 = spec_router.generate_candidates("让程序多加一个 2", previous_ir=ir)
    c2 = spec_router.generate_candidates("让程序多加一个 2", previous_ir=ir)
    assert [c.route_id for c in c1] == [c.route_id for c in c2]
    assert [c.prior_score for c in c1] == [c.prior_score for c in c2]


# ── 10. RuntimeResult 包含完整审计链 ─────────────────────────────────────────
@needs_compiler
def test_speculative_result_contains_full_audit_trail(rt):
    ir = make_two_sum_ir()
    result = rt.run("让程序多加一个 2", previous_ir=ir,
                    expected_output="4\n", speculative=True)
    assert result.all_candidates is not None and len(result.all_candidates) >= 3
    assert result.executed_candidates is not None and len(result.executed_candidates) >= 2
    assert result.selected_candidate is not None
    assert result.rejected_candidates is not None
    assert result.route_memory_updates is not None
