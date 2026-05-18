import sys
import os
import shutil
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jianmu.runtime import Runtime
from jianmu.ir import ProgramIR, SumExpression, Variable
from jianmu.experts import ConsistencyCheckExpert
from jianmu.intent_router import IntentRouter

HAS_COMPILER = bool(
    shutil.which("gcc") or shutil.which("clang") or
    shutil.which("gcc", path=os.environ.get("PATH","") + os.pathsep + "/data/data/com.termux/files/usr/bin") or
    shutil.which("clang", path=os.environ.get("PATH","") + os.pathsep + "/data/data/com.termux/files/usr/bin")
)
needs_compiler = pytest.mark.skipif(not HAS_COMPILER, reason="gcc/clang not found")


@pytest.fixture(autouse=True)
def fresh_runtime(tmp_path):
    """Each test gets a Runtime with a fresh cache."""
    rt = Runtime()
    rt._cache._path = str(tmp_path / "trace_cache.json")
    yield rt


# ── 1. 两数求和 ──────────────────────────────────────────────────────────────
@needs_compiler
def test_generate_two_sum_program(fresh_runtime):
    r = fresh_runtime.run("生成两个 int 相加并打印")
    assert r.sandbox_result.stdout.strip() == "2"


# ── 2. 扩展三数 ──────────────────────────────────────────────────────────────
@needs_compiler
def test_expand_two_sum_to_three_sum(fresh_runtime):
    r1 = fresh_runtime.run("生成两个 int 相加并打印")
    ir = ProgramIR.from_dict(r1.program_ir)
    r2 = fresh_runtime.run("把两个整数相加改成三个整数相加", previous_ir=ir)
    assert r2.sandbox_result.stdout.strip() == "3"


# ── 3. 扩展四数 ──────────────────────────────────────────────────────────────
@needs_compiler
def test_expand_to_four_sum(fresh_runtime):
    r1 = fresh_runtime.run("生成两个 int 相加并打印")
    ir2 = ProgramIR.from_dict(r1.program_ir)
    r2 = fresh_runtime.run("把两个整数相加改成三个整数相加", previous_ir=ir2)
    ir3 = ProgramIR.from_dict(r2.program_ir)
    r3 = fresh_runtime.run("扩展成四个整数相加", previous_ir=ir3)
    assert r3.sandbox_result.stdout.strip() == "4"


# ── 4. 中文变体归一化 ─────────────────────────────────────────────────────────
def test_chinese_variants_same_intent():
    router = IntentRouter()
    variants = [
        "写一个 C 程序，定义两个整数，都是 1，然后相加并打印结果",
        "生成两个 int 相加并打印",
        "让它算三个 1 的和",
        "扩展成四个整数相加",
    ]
    for text in variants[:2]:
        intent = router.parse(text)
        assert intent["operation"] == "sum"
        assert intent.get("var_count") == 2 or intent.get("target_var_count") == 2

    intent3 = router.parse("让它算三个 1 的和")
    assert intent3["operation"] == "sum"
    n3 = intent3.get("var_count") or intent3.get("target_var_count")
    assert n3 == 3

    intent4 = router.parse("扩展成四个整数相加")
    n4 = intent4.get("var_count") or intent4.get("target_var_count")
    assert n4 == 4


# ── 5. 编译运行输出 ───────────────────────────────────────────────────────────
@needs_compiler
def test_compile_and_run_output(fresh_runtime):
    for text, expected in [
        ("生成两个 int 相加并打印", "2"),
        ("让它算三个 1 的和", "3"),
    ]:
        r = fresh_runtime.run(text)
        assert r.sandbox_result.compile_success
        assert r.sandbox_result.stdout.strip() == expected


# ── 6. TraceCache hit ────────────────────────────────────────────────────────
@needs_compiler
def test_trace_cache_hit(fresh_runtime):
    r1 = fresh_runtime.run("生成两个 int 相加并打印")
    assert not r1.cache_hit
    r2 = fresh_runtime.run("生成两个 int 相加并打印")
    assert r2.cache_hit


# ── 7. 确定性重放 ─────────────────────────────────────────────────────────────
@needs_compiler
def test_deterministic_replay(fresh_runtime):
    r1 = fresh_runtime.run("生成两个 int 相加并打印")
    r2 = fresh_runtime.run("生成两个 int 相加并打印")  # cache hit
    assert r1.generated_code == r2.generated_code


# ── 8. 无硬编码三数/四数模板 ──────────────────────────────────────────────────
def test_no_hardcoded_three_or_four_sum_template():
    forbidden = [
        "generate_three_sum_template",
        "generate_four_sum_template",
        "three_sum_template",
        "four_sum_template",
    ]
    src_dir = os.path.join(os.path.dirname(__file__), "..", "jianmu")
    for fname in os.listdir(src_dir):
        if not fname.endswith(".py"):
            continue
        content = open(os.path.join(src_dir, fname)).read()
        for token in forbidden:
            assert token not in content, f"Forbidden template '{token}' found in {fname}"


# ── 9. ConsistencyCheckExpert 检测未定义变量 ──────────────────────────────────
def test_invalid_variable_detection_or_repair():
    ir = ProgramIR(
        variables=[Variable("a"), Variable("b")],
        expression=SumExpression(operands=["a", "b", "z"]),  # z 未定义
    )
    with pytest.raises(ValueError, match="z"):
        ConsistencyCheckExpert().apply(ir)
