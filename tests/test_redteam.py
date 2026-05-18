import sys
import os
import shutil
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jianmu.runtime import Runtime
from jianmu.ir import ProgramIR, Variable, SumExpression
from jianmu.experts import ExpandSumExpert, ConsistencyCheckExpert
from jianmu.emitter_c import CEmitter

HAS_COMPILER = bool(
    shutil.which("gcc") or shutil.which("clang") or
    shutil.which("gcc", path=os.environ.get("PATH", "") + os.pathsep + "/data/data/com.termux/files/usr/bin") or
    shutil.which("clang", path=os.environ.get("PATH", "") + os.pathsep + "/data/data/com.termux/files/usr/bin")
)
needs_compiler = pytest.mark.skipif(not HAS_COMPILER, reason="gcc/clang not found")


@pytest.fixture
def rt(tmp_path):
    r = Runtime()
    r._cache._path = str(tmp_path / "trace_cache.json")
    return r


# ── 1. 无 generate_three/four_sum_template 函数 ───────────────────────────────
def test_no_generate_three_sum_template_function():
    forbidden = ["generate_three_sum_template", "generate_four_sum_template"]
    src_dir = os.path.join(os.path.dirname(__file__), "..", "jianmu")
    for fname in os.listdir(src_dir):
        if not fname.endswith(".py"):
            continue
        content = open(os.path.join(src_dir, fname)).read()
        for token in forbidden:
            assert token not in content, f"Forbidden: '{token}' in {fname}"


# ── 2. 三数和四数共享相同专家类型，只是参数不同 ────────────────────────────────
@needs_compiler
def test_three_and_four_share_same_expert_path_prefix(rt):
    r2 = rt.run("生成两个 int 相加并打印")
    ir2 = ProgramIR.from_dict(r2.program_ir)
    r3 = rt.run("把两个整数相加改成三个整数相加", previous_ir=ir2)
    ir3 = ProgramIR.from_dict(r3.program_ir)
    r4 = rt.run("扩展成四个整数相加", previous_ir=ir3)

    # Both expand paths must use ExpandSumExpert
    assert "ExpandSumExpert" in r3.activated_experts
    assert "ExpandSumExpert" in r4.activated_experts
    # Expert type list must be identical (same path, different param)
    assert r3.activated_experts == r4.activated_experts


# ── 3. 生成代码包含正确操作数 ─────────────────────────────────────────────────
@needs_compiler
def test_generated_code_contains_expected_operands(rt):
    r2 = rt.run("生成两个 int 相加并打印")
    ir2 = ProgramIR.from_dict(r2.program_ir)
    r3 = rt.run("把两个整数相加改成三个整数相加", previous_ir=ir2)
    ir3 = ProgramIR.from_dict(r3.program_ir)
    r4 = rt.run("扩展成四个整数相加", previous_ir=ir3)

    assert "a + b + c" in r3.generated_code
    assert "a + b + c + d" in r4.generated_code


# ── 4. 不同 previous_ir 不能错误命中同一缓存 ──────────────────────────────────
@needs_compiler
def test_cache_key_changes_with_program_state(rt):
    r2 = rt.run("生成两个 int 相加并打印")
    ir2 = ProgramIR.from_dict(r2.program_ir)
    r3 = rt.run("把两个整数相加改成三个整数相加", previous_ir=ir2)
    ir3 = ProgramIR.from_dict(r3.program_ir)

    # Expanding from ir2 (2-var) vs ir3 (3-var) with same intent must be different cache keys
    r4_from_2 = rt.run("扩展成四个整数相加", previous_ir=ir2)
    r4_from_3 = rt.run("扩展成四个整数相加", previous_ir=ir3)

    # Both should be cache miss on first call (different keys)
    assert not r4_from_2.cache_hit
    assert not r4_from_3.cache_hit
    # But generated code must differ (one starts from 2-var, other from 3-var)
    # Both should produce 4-var result since ExpandSumExpert now sets absolute target
    assert r4_from_2.generated_code == r4_from_3.generated_code  # same target=4
    # Second call with same ir2 must hit cache
    r4_from_2_again = rt.run("扩展成四个整数相加", previous_ir=ir2)
    assert r4_from_2_again.cache_hit


# ── 5. ConsistencyCheckExpert 拒绝未定义操作数 ────────────────────────────────
def test_consistency_check_rejects_undefined_operand():
    ir = ProgramIR(
        variables=[Variable("a"), Variable("b")],
        expression=SumExpression(operands=["a", "b", "z"]),
    )
    with pytest.raises(ValueError, match="z"):
        ConsistencyCheckExpert().apply(ir)


# ── 6. README 包含明确 non-claims ─────────────────────────────────────────────
def test_readme_non_claims_exist():
    readme = open(os.path.join(os.path.dirname(__file__), "..", "README.md")).read()
    required = [
        "NOT prove",
        "LLM",
        "general",
    ]
    for token in required:
        assert token in readme, f"README missing non-claim keyword: '{token}'"


# ── 7. ExpandSumExpert 支持缩减（target < current）────────────────────────────
def test_expand_sum_expert_supports_reduction():
    ir = ProgramIR(
        variables=[Variable("a"), Variable("b"), Variable("c")],
        expression=SumExpression(operands=["a", "b", "c"]),
    )
    result = ExpandSumExpert(2).apply(ir)
    assert len(result.variables) == 2
    assert result.expression.operands == ["a", "b"]


# ── 8. deterministic_replay 真正比较代码字符串 ────────────────────────────────
def test_deterministic_replay_compares_code_not_stdout():
    from jianmu.scoring import Scorer
    from jianmu.sandbox import SandboxResult

    fake_result = SandboxResult(
        compiler="gcc", compile_success=True, run_success=True,
        stdout="3\n", stderr="", returncode=0, error_type="", command=""
    )
    scorer = Scorer()

    # Same code → deterministic_replay = 1
    r1 = scorer.score(fake_result, "3\n", previous_code="code_A", current_code="code_A")
    assert r1.deterministic_replay == 1

    # Different code → deterministic_replay = 0, even if stdout matches
    r2 = scorer.score(fake_result, "3\n", previous_code="code_A", current_code="code_B")
    assert r2.deterministic_replay == 0


# ── 9. 数值泛化：1加2加3 输出 6 ───────────────────────────────────────────────
@needs_compiler
def test_value_generalization_1_2_3_outputs_6(rt):
    r = rt.run("1加2加3")
    assert r.sandbox_result.stdout.strip() == "6"


# ── 10. 定义三个整数 1 2 3 输出 6 ─────────────────────────────────────────────
@needs_compiler
def test_define_three_integers_1_2_3_outputs_6(rt):
    r = rt.run("定义三个整数 1 2 3 并输出和")
    assert r.sandbox_result.stdout.strip() == "6"


# ── 11. 扩展时新增变量值正确传递 ──────────────────────────────────────────────
@needs_compiler
def test_expand_add_value_outputs_correct_sum(rt):
    # Start: 1+1=2, then add one more with value 2 → 1+1+2=4
    r1 = rt.run("生成两个 int 相加并打印")
    ir1 = ProgramIR.from_dict(r1.program_ir)
    r2 = rt.run("让程序多加一个 2", previous_ir=ir1)
    assert r2.sandbox_result.stdout.strip() == "4"


# ── 12. 英文 sum of three numbers ─────────────────────────────────────────────
@needs_compiler
def test_english_sum_of_three_numbers(rt):
    r = rt.run("sum of three numbers")
    assert r.sandbox_result.stdout.strip() == "3"


# ── 13. 扩展为 解析 target_var_count ──────────────────────────────────────────
def test_expand_phrase_target_num_after_扩展为():
    from jianmu.intent_router import IntentRouter
    intent = IntentRouter().parse("把两个加数扩展为三个加数")
    assert intent["action"] == "expand_sum_program"
    assert intent["target_var_count"] == 3


# ── 14. 无 trace_cache.json 提交到仓库 ────────────────────────────────────────
def test_no_cache_artifact_committed():
    cache_path = os.path.join(os.path.dirname(__file__), "..", "data", "trace_cache.json")
    gitignore_path = os.path.join(os.path.dirname(__file__), "..", ".gitignore")
    assert os.path.exists(gitignore_path), ".gitignore missing"
    content = open(gitignore_path).read()
    assert "trace_cache.json" in content, "trace_cache.json not in .gitignore"


# ── 15. CRITIQUE.md 不含已修复 bug 的旧批评 ───────────────────────────────────
def test_critique_not_stale():
    critique_path = os.path.join(os.path.dirname(__file__), "..", "CRITIQUE.md")
    content = open(critique_path).read()
    # The old stale claim should no longer appear as an active bug
    assert "只比较 stdout" not in content or "已修复" in content, \
        "CRITIQUE.md still contains stale deterministic_replay bug without marking it fixed"


# ── 16. Scoring correctness_score 满分可达 1.0 ────────────────────────────────
def test_scoring_correctness_score_can_reach_1():
    from jianmu.scoring import Scorer
    from jianmu.sandbox import SandboxResult
    fake = SandboxResult(
        compiler="gcc", compile_success=True, run_success=True,
        stdout="3\n", stderr="", returncode=0, error_type="", command=""
    )
    r = Scorer().score(fake, "3\n", previous_code="x", current_code="x",
                       cache_hit=True, consistency_ok=True)
    assert r.correctness_score == 1.0
    assert r.runtime_score == 1.0
    assert r.total_score == 1.0
