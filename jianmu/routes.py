from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RouteCandidate:
    route_id: str
    source: str          # "rule_candidate" | "memory_prior" | "fallback"
    intent: dict
    expert_plan: List[str]
    prior_score: float
    requires_previous_ir: bool = False
    expected_output: Optional[str] = None
    rationale: str = ""


@dataclass
class CandidateExecutionResult:
    candidate: RouteCandidate
    program_ir: Optional[dict]
    generated_code: str
    sandbox_result: object
    score_report: object
    success: bool
    final_score: float
    errors: List[str] = field(default_factory=list)
