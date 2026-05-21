from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class StateInventoryReport:
    branchchain_state_found: bool
    branch_neuron_state_found: bool
    router_scoring_state_found: bool
    root_colony_state_found: bool
    root_lifecycle_state_found: bool
    nutrient_memory_state_found: bool
    toxic_memory_state_found: bool
    boundary_probe_state_found: bool
    evaluation_summary_only_found: bool
    unavailable_state_components: List[str]
    serializable_component_count: int
    nonserializable_component_count: int
    required_for_full_state: List[str]
    missing_for_full_state: List[str]
    inventory_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_state_inventory_audit(source_records_dir: str | Path | None = None) -> Dict[str, Any]:
    source_records_dir = Path(source_records_dir) if source_records_dir else None
    branch_neuron_state_found = _has_dataclass_fields("jianmu.self_learning.branchchain.branch_neuron", "BranchNeuron")
    branchchain_state_found = _has_attr("jianmu.self_learning.darwinforge.population", "LayerPreservedPopulation")
    root_colony_state_found = _has_to_dict("jianmu.self_learning.darwinforge.root_colony", "RootColony")
    root_lifecycle_state_found = _has_to_dict("jianmu.self_learning.darwinforge.root_lifecycle", "RootLifecycleState")
    nutrient_memory_state_found = _has_to_dict("jianmu.self_learning.darwinforge.rootforge", "NutrientSignal")
    toxic_memory_state_found = _has_to_dict("jianmu.self_learning.darwinforge.toxic_nutrient", "NutrientSignal")
    boundary_probe_state_found = bool(source_records_dir and (source_records_dir / "persisted_router_metrics.json").exists())
    evaluation_summary_only_found = bool(source_records_dir and any(source_records_dir.glob("*.json")))

    required = [
        "trained_branch_population",
        "trained_root_colonies",
        "root_lifecycle_runtime_states",
        "nutrient_toxic_runtime_memory",
    ]
    missing = []
    if not _record_exists(source_records_dir, "state/full_router_state.json"):
        missing.append("trained_branch_population")
    if not _record_exists(source_records_dir, "state/full_root_state.json"):
        missing.append("trained_root_colonies")
    if not _record_exists(source_records_dir, "state/root_lifecycle_state.json"):
        missing.append("root_lifecycle_runtime_states")
    if not _record_exists(source_records_dir, "state/nutrient_toxic_memory.json"):
        missing.append("nutrient_toxic_runtime_memory")

    found_flags = [
        branchchain_state_found,
        branch_neuron_state_found,
        root_colony_state_found,
        root_lifecycle_state_found,
        nutrient_memory_state_found,
        toxic_memory_state_found,
        boundary_probe_state_found,
    ]
    report = StateInventoryReport(
        branchchain_state_found=branchchain_state_found,
        branch_neuron_state_found=branch_neuron_state_found,
        router_scoring_state_found=branch_neuron_state_found,
        root_colony_state_found=root_colony_state_found,
        root_lifecycle_state_found=root_lifecycle_state_found,
        nutrient_memory_state_found=nutrient_memory_state_found,
        toxic_memory_state_found=toxic_memory_state_found,
        boundary_probe_state_found=boundary_probe_state_found,
        evaluation_summary_only_found=evaluation_summary_only_found,
        unavailable_state_components=missing,
        serializable_component_count=sum(1 for flag in found_flags if flag),
        nonserializable_component_count=len(missing),
        required_for_full_state=required,
        missing_for_full_state=missing,
        inventory_passed=branchchain_state_found and root_colony_state_found and branch_neuron_state_found,
    )
    return report.to_dict()


def write_state_inventory(path: str | Path, report: Dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _has_attr(module_name: str, attr_name: str) -> bool:
    try:
        module = __import__(module_name, fromlist=[attr_name])
        return hasattr(module, attr_name)
    except Exception:
        return False


def _has_to_dict(module_name: str, attr_name: str) -> bool:
    try:
        cls = getattr(__import__(module_name, fromlist=[attr_name]), attr_name)
        return hasattr(cls, "to_dict")
    except Exception:
        return False


def _has_dataclass_fields(module_name: str, attr_name: str) -> bool:
    try:
        cls = getattr(__import__(module_name, fromlist=[attr_name]), attr_name)
        return hasattr(cls, "__dataclass_fields__")
    except Exception:
        return False


def _record_exists(source_records_dir: Path | None, relpath: str) -> bool:
    return bool(source_records_dir and (source_records_dir / relpath).exists())
