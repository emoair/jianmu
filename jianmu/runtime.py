import copy
from dataclasses import dataclass, field
from typing import List, Optional

from jianmu.intent_router import IntentRouter
from jianmu.ir import ProgramIR
from jianmu.experts import (
    IncludeExpert, VariableDefinitionExpert, SumExpressionExpert,
    PrintfExpert, MainFunctionExpert, ExpandSumExpert, ConsistencyCheckExpert,
)
from jianmu.emitter_c import CEmitter
from jianmu.sandbox import Sandbox
from jianmu.scoring import Scorer
from jianmu.trace_cache import TraceCache


@dataclass
class RuntimeResult:
    input: str
    normalized_intent: dict
    cache_hit: bool
    activated_experts: List[str]
    program_ir: dict
    generated_code: str
    sandbox_result: object
    score_report: object
    errors: List[str] = field(default_factory=list)


class Runtime:
    def __init__(self):
        self._router = IntentRouter()
        self._emitter = CEmitter()
        self._sandbox = Sandbox()
        self._scorer = Scorer()
        self._cache = TraceCache()

    def run(self, user_input: str, previous_ir: Optional[ProgramIR] = None,
            expected_output: str = None) -> RuntimeResult:
        errors = []
        prev_var_count = len(previous_ir.variables) if previous_ir else None
        intent = self._router.parse(user_input, previous_var_count=prev_var_count)
        prev_ir_dict = previous_ir.to_dict() if previous_ir else None

        # Cache lookup
        cached = self._cache.get(intent, prev_ir_dict)
        if cached:
            sandbox = self._sandbox.run(cached["generated_code"])
            score = self._scorer.score(
                sandbox, cached["expected_output"],
                previous_code=cached["generated_code"],
                current_code=cached["generated_code"],
                cache_hit=True,
            )
            return RuntimeResult(
                input=user_input, normalized_intent=intent, cache_hit=True,
                activated_experts=cached["activated_experts"],
                program_ir=cached["program_ir"],
                generated_code=cached["generated_code"],
                sandbox_result=sandbox, score_report=score,
            )

        # Build IR
        activated = []
        consistency_ok = True

        if intent["action"] == "generate_sum_program":
            ir = ProgramIR()
            n = intent["var_count"]
            values = intent.get("values") or [1] * n
            ir = IncludeExpert().apply(ir);                              activated.append("IncludeExpert")
            ir = VariableDefinitionExpert(n, values).apply(ir);          activated.append("VariableDefinitionExpert")
            ir = SumExpressionExpert().apply(ir);                        activated.append("SumExpressionExpert")
            ir = PrintfExpert().apply(ir);                               activated.append("PrintfExpert")
            ir = MainFunctionExpert().apply(ir);                         activated.append("MainFunctionExpert")

        elif intent["action"] == "expand_sum_program":
            ir = copy.deepcopy(previous_ir) if previous_ir else ProgramIR()
            target = intent["target_var_count"]
            if target is None:
                target = len(ir.variables) + 1
            new_val = intent.get("new_value", 1)
            ir = IncludeExpert().apply(ir);                              activated.append("IncludeExpert")
            ir = ExpandSumExpert(target, new_value=new_val).apply(ir);   activated.append("ExpandSumExpert")
            ir = PrintfExpert().apply(ir);                               activated.append("PrintfExpert")
            ir = MainFunctionExpert().apply(ir);                         activated.append("MainFunctionExpert")

        else:
            errors.append(f"Unknown action: {intent['action']}")
            ir = ProgramIR()

        # Consistency check
        try:
            ConsistencyCheckExpert().apply(ir)
            activated.append("ConsistencyCheckExpert")
        except ValueError as e:
            errors.append(str(e))
            consistency_ok = False

        code = self._emitter.emit(ir)
        sandbox = self._sandbox.run(code)

        # expected_output: use sum(values) not len(variables)
        if expected_output:
            exp_out = expected_output
        else:
            exp_out = f"{sum(v.value for v in ir.variables)}\n"

        # Re-emit to verify byte-level determinism
        code_replay = self._emitter.emit(ir)
        score = self._scorer.score(
            sandbox, exp_out,
            previous_code=code, current_code=code_replay,
            cache_hit=False, consistency_ok=consistency_ok,
        )

        record = {
            "normalized_intent": intent,
            "activated_experts": activated,
            "program_ir": ir.to_dict(),
            "generated_code": code,
            "expected_output": exp_out,
            "sandbox_result_summary": {
                "compile_success": sandbox.compile_success,
                "run_success": sandbox.run_success,
                "stdout": sandbox.stdout,
            },
            "score": score.total_score,
        }
        if score.correctness_score == 1.0:
            self._cache.put(intent, prev_ir_dict, record)

        return RuntimeResult(
            input=user_input, normalized_intent=intent, cache_hit=False,
            activated_experts=activated, program_ir=ir.to_dict(),
            generated_code=code, sandbox_result=sandbox, score_report=score,
            errors=errors,
        )
