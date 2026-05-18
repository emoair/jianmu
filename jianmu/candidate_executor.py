import copy
import string
from typing import List, Optional

from jianmu.ir import ProgramIR, Variable, SumExpression
from jianmu.routes import RouteCandidate, CandidateExecutionResult
from jianmu.experts import (
    IncludeExpert, VariableDefinitionExpert, SumExpressionExpert,
    PrintfExpert, MainFunctionExpert, ExpandSumExpert, ConsistencyCheckExpert,
    ReplaceOperandExpert,
)
from jianmu.emitter_c import CEmitter
from jianmu.sandbox import Sandbox
from jianmu.scoring import Scorer


class CandidateExecutor:
    def __init__(self):
        self._emitter = CEmitter()
        self._sandbox = Sandbox()
        self._scorer = Scorer()

    def execute(
        self,
        candidate: RouteCandidate,
        previous_ir: Optional[ProgramIR] = None,
        expected_output: Optional[str] = None,
    ) -> CandidateExecutionResult:
        errors = []
        consistency_ok = True
        ir = None

        try:
            action = candidate.intent.get("action")

            if action == "expand_sum_program":
                if previous_ir is None:
                    raise ValueError("append_literal requires previous_ir")
                ir = copy.deepcopy(previous_ir)
                target = candidate.intent.get("target_var_count", len(ir.variables) + 1)
                new_val = candidate.intent.get("new_value", 1)
                ir = IncludeExpert().apply(ir)
                ir = ExpandSumExpert(target, new_value=new_val).apply(ir)
                ir = PrintfExpert().apply(ir)
                ir = MainFunctionExpert().apply(ir)

            elif action == "generate_sum_program":
                ir = ProgramIR()
                n = candidate.intent.get("var_count", 2)
                values = candidate.intent.get("values") or [1] * n
                ir = IncludeExpert().apply(ir)
                ir = VariableDefinitionExpert(n, values).apply(ir)
                ir = SumExpressionExpert().apply(ir)
                ir = PrintfExpert().apply(ir)
                ir = MainFunctionExpert().apply(ir)

            elif action == "replace_last_operand":
                if previous_ir is None:
                    raise ValueError("replace_last_operand requires previous_ir")
                ir = copy.deepcopy(previous_ir)
                new_val = candidate.intent.get("new_value", 1)
                ir = IncludeExpert().apply(ir)
                ir = ReplaceOperandExpert(new_val).apply(ir)
                ir = PrintfExpert().apply(ir)
                ir = MainFunctionExpert().apply(ir)

            else:
                raise ValueError(f"Unknown action: {action}")

            # Consistency check
            try:
                ConsistencyCheckExpert().apply(ir)
            except ValueError as e:
                errors.append(str(e))
                consistency_ok = False

        except Exception as e:
            errors.append(str(e))
            # Return a failed result with no compilation
            from jianmu.sandbox import SandboxResult
            fake = SandboxResult(
                compiler="", compile_success=False, run_success=False,
                stdout="", stderr=str(e), returncode=-1,
                error_type="setup_error", command="",
            )
            score = self._scorer.score(fake, expected_output or "", consistency_ok=False)
            return CandidateExecutionResult(
                candidate=candidate, program_ir=None,
                generated_code="", sandbox_result=fake,
                score_report=score, success=False,
                final_score=0.0, errors=errors,
            )

        code = self._emitter.emit(ir)
        sandbox = self._sandbox.run(code)

        exp_out = expected_output or f"{sum(v.value for v in ir.variables)}\n"
        code_replay = self._emitter.emit(ir)
        score = self._scorer.score(
            sandbox, exp_out,
            previous_code=code, current_code=code_replay,
            consistency_ok=consistency_ok,
        )

        success = score.correctness_score == 1.0
        return CandidateExecutionResult(
            candidate=candidate,
            program_ir=ir.to_dict(),
            generated_code=code,
            sandbox_result=sandbox,
            score_report=score,
            success=success,
            final_score=score.correctness_score,
            errors=errors,
        )
