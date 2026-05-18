import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jianmu.runtime import Runtime
from jianmu.ir import ProgramIR

rt = Runtime()
rt._cache.clear()

print("=" * 50)
print("Demo 1: 两数求和")
r1 = rt.run("生成两个 int 相加并打印")
print("Code:\n" + r1.generated_code)
print("stdout:", repr(r1.sandbox_result.stdout))
print("score:", r1.score_report.total_score)

print("=" * 50)
print("Demo 2: 扩展三数求和")
ir2 = ProgramIR.from_dict(r1.program_ir)
r2 = rt.run("把两个整数相加改成三个整数相加", previous_ir=ir2)
print("Code:\n" + r2.generated_code)
print("stdout:", repr(r2.sandbox_result.stdout))
print("score:", r2.score_report.total_score)

print("=" * 50)
print("Demo 3: 扩展四数求和")
ir3 = ProgramIR.from_dict(r2.program_ir)
r3 = rt.run("扩展成四个整数相加", previous_ir=ir3)
print("Code:\n" + r3.generated_code)
print("stdout:", repr(r3.sandbox_result.stdout))
print("score:", r3.score_report.total_score)

print("=" * 50)
print("Demo 4: 第二次运行三数 (cache hit)")
ir2b = ProgramIR.from_dict(r1.program_ir)
r4 = rt.run("把两个整数相加改成三个整数相加", previous_ir=ir2b)
print("cache_hit:", r4.cache_hit)
print("stdout:", repr(r4.sandbox_result.stdout))
print("score:", r4.score_report.total_score)
