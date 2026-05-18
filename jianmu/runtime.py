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
from jianmu.routes import RouteCandidate, CandidateExecutionResult
from jianmu.speculative_router import SpeculativeRouter
from jianmu.candidate_executor import CandidateExecutor
from jianmu.route_memory import RouteMemory


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
    # v0.4 speculative fields (None in deterministic mode)
    all_candidates: Optional[List[RouteCandidate]] = None
    executed_candidates: Optional[List[CandidateExecutionResult]] = None
    selected_candidate: Optional[CandidateExecutionResult] = None
    rejected_candidates: Optional[List[CandidateExecutionResult]] = None
    route_memory_updates: Optional[dict] = None


class Runtime:
    def __init__(self):
        self._router = IntentRouter()
        self._emitter = CEmitter()
        self._sandbox = Sandbox()
        self._scorer = Scorer()
        self._cache = TraceCache()
        self._spec_router = SpeculativeRouter()
        self._executor = CandidateExecutor()
        self._memory = RouteMemory()

    # ── v0.3 deterministic path (preserved) ──────────────────────────────────
    def run(self, user_input: str, previous_ir: Optional[ProgramIR] = None,
            expected_output: str = None, speculative: bool = False) -> RuntimeResult:
        if speculative:
            return self._run_speculative(user_input, previous_ir, expected_output)
        return self._run_deterministic(user_input, previous_ir, expected_output)

    def _run_deterministic(self, user_input: str,
                           previous_ir: Optional[ProgramIR],
                           expected_output: Optional[str]) -> RuntimeResult:
        errors = []
        prev_var_count = len(previous_ir.variables) if previous_ir else None
        intent = self._router.parse(user_input, previous_var_count=prev_var_count)
        prev_ir_dict = previous_ir.to_dict() if previous_ir else None

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

        try:
            ConsistencyCheckExpert().apply(ir)
            activated.append("ConsistencyCheckExpert")
        except ValueError as e:
            errors.append(str(e))
            consistency_ok = False

        code = self._emitter.emit(ir)
        sandbox = self._sandbox.run(code)
        exp_out = expected_output or f"{sum(v.value for v in ir.variables)}\n"
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

    # ── v0.4 speculative path ─────────────────────────────────────────────────
    def _run_speculative(self, user_input: str,
                         previous_ir: Optional[ProgramIR],
                         expected_output: Optional[str],
                         top_k: int = 3) -> RuntimeResult:
        has_prev = previous_ir is not None

        # 1. Generate candidates
        candidates = self._spec_router.generate_candidates(user_input, previous_ir)

        # 2. Boost prior_score from RouteMemory
        for c in candidates:
            boost = self._memory.get_prior_boost(user_input, has_prev, c.route_id)
            c.prior_score = round(min(1.0, c.prior_score + boost), 4)

        # 3. Sort by prior_score descending, execute top_k
        candidates.sort(key=lambda c: c.prior_score, reverse=True)
        to_execute = candidates[:top_k]

        # 4. Execute each candidate
        executed: List[CandidateExecutionResult] = []
        for cand in to_execute:
            result = self._executor.execute(cand, previous_ir, expected_output)
            executed.append(result)

        # 5. Select winner: highest correctness_score, must be 1.0 if any succeed
        executed.sort(key=lambda r: r.final_score, reverse=True)
        winner = executed[0]
        losers = executed[1:]

        # 6. Update RouteMemory
        memory_updates = {}
        self._memory.record(user_input, has_prev, winner.candidate.route_id,
                            winner.success, winner.final_score)
        memory_updates[winner.candidate.route_id] = {"success": winner.success, "score": winner.final_score}
        for loser in losers:
            self._memory.record(user_input, has_prev, loser.candidate.route_id,
                                loser.success, loser.final_score)
            memory_updates[loser.candidate.route_id] = {"success": loser.success, "score": loser.final_score}

        # 7. Write TraceCache only for winner with correctness_score == 1.0
        if winner.success and winner.program_ir:
            intent_key = winner.candidate.intent
            prev_ir_dict = previous_ir.to_dict() if previous_ir else None
            record = {
                "normalized_intent": intent_key,
                "activated_experts": winner.candidate.expert_plan,
                "program_ir": winner.program_ir,
                "generated_code": winner.generated_code,
                "expected_output": winner.sandbox_result.stdout,
                "sandbox_result_summary": {
                    "compile_success": winner.sandbox_result.compile_success,
                    "run_success": winner.sandbox_result.run_success,
                    "stdout": winner.sandbox_result.stdout,
                },
                "score": winner.final_score,
            }
            self._cache.put(intent_key, prev_ir_dict, record)

        return RuntimeResult(
            input=user_input,
            normalized_intent=winner.candidate.intent,
            cache_hit=False,
            activated_experts=winner.candidate.expert_plan,
            program_ir=winner.program_ir or {},
            generated_code=winner.generated_code,
            sandbox_result=winner.sandbox_result,
            score_report=winner.score_report,
            errors=winner.errors,
            all_candidates=candidates,
            executed_candidates=executed,
            selected_candidate=winner,
            rejected_candidates=losers,
            route_memory_updates=memory_updates,
        )
