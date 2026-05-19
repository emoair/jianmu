from dataclasses import dataclass
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.branch_types import BranchPath


@dataclass
class CandidateGenome:
    genome_id: str
    branch_path: BranchPath
    atomic_expert_plan: List[str]
    slot_binding_policy: str
    target_builder_policy: str
    mutation_count: int = 0
    parent_id: Optional[str] = None
    generation: int = 0

    def to_dict(self) -> Dict:
        return {
            "genome_id": self.genome_id,
            "branch_path": self.branch_path.to_dict(),
            "atomic_expert_plan": list(self.atomic_expert_plan),
            "slot_binding_policy": self.slot_binding_policy,
            "target_builder_policy": self.target_builder_policy,
            "mutation_count": self.mutation_count,
            "parent_id": self.parent_id,
            "generation": self.generation,
        }

    @classmethod
    def from_dict(cls, payload: Dict) -> "CandidateGenome":
        return cls(
            genome_id=payload["genome_id"],
            branch_path=BranchPath.from_dict(payload["branch_path"]),
            atomic_expert_plan=list(payload.get("atomic_expert_plan", [])),
            slot_binding_policy=payload.get("slot_binding_policy", ""),
            target_builder_policy=payload.get("target_builder_policy", ""),
            mutation_count=int(payload.get("mutation_count", 0)),
            parent_id=payload.get("parent_id"),
            generation=int(payload.get("generation", 0)),
        )


@dataclass
class CandidatePhenotype:
    genome_id: str
    target_ir_canonical: Optional[str]
    c_program: Optional[str]
    expected_output_pred: Optional[str]
    unsupported_pred: bool
    failure_reason: Optional[str]

    def to_dict(self) -> Dict:
        return {
            "genome_id": self.genome_id,
            "target_ir_canonical": self.target_ir_canonical,
            "c_program": self.c_program,
            "expected_output_pred": self.expected_output_pred,
            "unsupported_pred": self.unsupported_pred,
            "failure_reason": self.failure_reason,
        }


@dataclass
class CandidateRecord:
    genome: CandidateGenome
    phenotype: CandidatePhenotype
    fitness_report: object

    def to_dict(self) -> Dict:
        return {
            "genome": self.genome.to_dict(),
            "phenotype": self.phenotype.to_dict(),
            "fitness_report": self.fitness_report.to_dict()
            if hasattr(self.fitness_report, "to_dict")
            else self.fitness_report,
        }

