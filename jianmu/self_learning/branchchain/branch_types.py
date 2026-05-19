from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BranchDecision:
    layer_name: str
    candidates: List[str]
    selected: str
    confidence: int
    neuron_id: str
    evidence: Dict
    reward: float = 0.0
    can_continue: bool = True
    reject_reason: Optional[str] = None
    confidence_margin: Optional[int] = None
    gate_threshold: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "layer_name": self.layer_name,
            "candidates": list(self.candidates),
            "selected": self.selected,
            "confidence": self.confidence,
            "neuron_id": self.neuron_id,
            "evidence": dict(self.evidence),
            "reward": self.reward,
            "can_continue": self.can_continue,
            "reject_reason": self.reject_reason,
            "confidence_margin": self.confidence_margin,
            "gate_threshold": self.gate_threshold,
        }

    @classmethod
    def from_dict(cls, payload: Dict) -> "BranchDecision":
        return cls(
            layer_name=payload["layer_name"],
            candidates=list(payload.get("candidates", [])),
            selected=payload["selected"],
            confidence=int(payload.get("confidence", 0)),
            neuron_id=payload.get("neuron_id", ""),
            evidence=dict(payload.get("evidence", {})),
            reward=float(payload.get("reward", 0.0)),
            can_continue=bool(payload.get("can_continue", True)),
            reject_reason=payload.get("reject_reason"),
            confidence_margin=payload.get("confidence_margin"),
            gate_threshold=payload.get("gate_threshold"),
        )


@dataclass
class BranchPath:
    decisions: List[BranchDecision] = field(default_factory=list)
    route_confidence: int = 0
    atomic_experts: List[str] = field(default_factory=list)
    target_builder: str = ""
    early_exit: bool = False
    unsupported_reason: Optional[str] = None
    rejected_by_layer: Optional[str] = None
    reject_reason: Optional[str] = None
    reject_type: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "decisions": [decision.to_dict() for decision in self.decisions],
            "route_confidence": self.route_confidence,
            "atomic_experts": list(self.atomic_experts),
            "target_builder": self.target_builder,
            "early_exit": self.early_exit,
            "unsupported_reason": self.unsupported_reason,
            "rejected_by_layer": self.rejected_by_layer,
            "reject_reason": self.reject_reason,
            "reject_type": self.reject_type,
        }

    @classmethod
    def from_dict(cls, payload: Dict) -> "BranchPath":
        return cls(
            decisions=[BranchDecision.from_dict(item) for item in payload.get("decisions", [])],
            route_confidence=int(payload.get("route_confidence", 0)),
            atomic_experts=list(payload.get("atomic_experts", [])),
            target_builder=payload.get("target_builder", ""),
            early_exit=bool(payload.get("early_exit", False)),
            unsupported_reason=payload.get("unsupported_reason"),
            rejected_by_layer=payload.get("rejected_by_layer"),
            reject_reason=payload.get("reject_reason"),
            reject_type=payload.get("reject_type"),
        )


@dataclass
class PathExecutionResult:
    branch_path: BranchPath
    target_ir_canonical: Optional[str]
    expected_output_pred: Optional[str]
    compile_success: Optional[bool]
    run_success: Optional[bool]
    expected_output_match: bool
    target_ir_exact_match: bool
    reward: float
    failure_reason: Optional[str]

    def to_dict(self) -> Dict:
        return {
            "branch_path": self.branch_path.to_dict(),
            "target_ir_canonical": self.target_ir_canonical,
            "expected_output_pred": self.expected_output_pred,
            "compile_success": self.compile_success,
            "run_success": self.run_success,
            "expected_output_match": self.expected_output_match,
            "target_ir_exact_match": self.target_ir_exact_match,
            "reward": self.reward,
            "failure_reason": self.failure_reason,
        }
