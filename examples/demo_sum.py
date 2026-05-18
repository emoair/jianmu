import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jianmu.ir import ProgramIR, SumExpression, Variable
from jianmu.runtime import Runtime


def two_sum_ir():
    return ProgramIR(
        variables=[Variable("a", value=1), Variable("b", value=1)],
        expression=SumExpression(operands=["a", "b"]),
    )


def show_result(title, result):
    print("=" * 50)
    print(title)
    if result.selected_candidate:
        print("route:", result.selected_candidate.candidate.route_id)
    print("Code:\n" + result.generated_code)
    print("stdout:", repr(result.sandbox_result.stdout))
    print("score:", result.score_report.total_score)


rt = Runtime()
rt._cache.clear()

show_result(
    "Demo 1: Chinese-first generation with C/int/printf tokens",
    rt.run("定义三个 int，分别是 1、2、3，然后 printf 输出和", speculative=True),
)

show_result(
    "Demo 2: no-op wins on negated append",
    rt.run("不要多加2，保持不变", previous_ir=two_sum_ir(), speculative=True),
)

show_result(
    "Demo 3: replace wins over append",
    rt.run("把最后一个1改成2", previous_ir=two_sum_ir(), speculative=True),
)

show_result(
    "Demo 4: append multiple operands",
    rt.run("再加两个2", previous_ir=two_sum_ir(), speculative=True),
)
