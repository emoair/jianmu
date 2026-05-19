import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.datasets.large_architecture_aligned import load_jsonl
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


RECORD_DIR = Path("records/v0_6_8")
METRICS_PATH = RECORD_DIR / "large_dataset_smoke_metrics.json"
REPORT_PATH = RECORD_DIR / "large_dataset_smoke_report.md"
CANDIDATES_PATH = RECORD_DIR / "large_dataset_smoke_candidates.jsonl"


def run_smoke_benchmark(
    dataset_path: Path,
    sample_size: int = 800,
    seed: int = 42,
    population_per_layer: int = 8,
    top_k: int = 3,
) -> Dict:
    start_time = time.time()
    samples = load_jsonl(dataset_path)
    sampled = _sample_splits(samples, sample_size)
    population = LayerPreservedPopulation.initialize(population_per_layer=population_per_layer, seed=seed)
    synthesis = AtomicSynthesis()
    records = []
    split_rows = defaultdict(list)
    candidate_success = 0
    true_missing = 0
    early_reject_short = 0
    exact_match = 0
    ood_total = 0
    ood_rejected = 0
    ood_false_accept = 0

    for sample in sampled:
        features = extract_surface_features(sample["input_text"])
        genomes = population.sample_candidate_paths(features, top_k=top_k)
        candidate_success += bool(genomes)
        if not genomes:
            row = _empty_row(sample)
            records.append(row)
            split_rows[sample["split"]].append(row)
            continue
        genome = genomes[0]
        phenotype = synthesis.synthesize(genome, features)
        fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
        row = {
            "sample_id": sample["sample_id"],
            "split": sample["split"],
            "input_text": sample["input_text"],
            "input_mode": sample["input_mode"],
            "paraphrase_group": sample["paraphrase_group"],
            "supported": sample["supported"],
            "target_ir_true": sample.get("target_ir_canonical"),
            "target_ir_pred": phenotype.target_ir_canonical,
            "unsupported_pred": phenotype.unsupported_pred,
            "exact_match": fitness.target_ir_exact_match,
            "expected_output_match": fitness.expected_output_match,
            "early_exit": genome.branch_path.early_exit,
            "reject_type": genome.branch_path.reject_type,
            "rejected_by_layer": genome.branch_path.rejected_by_layer,
            "decision_count": len(genome.branch_path.decisions),
            "target_path_length": len(sample.get("target_branch_path", [])),
        }
        records.append(row)
        split_rows[sample["split"]].append(row)
        exact_match += int(fitness.target_ir_exact_match)
        if genome.branch_path.early_exit:
            early_reject_short += 1
        elif len(genome.branch_path.decisions) < len(sample.get("target_branch_path", [])):
            true_missing += 1
        if not sample["supported"]:
            ood_total += 1
            if phenotype.unsupported_pred:
                ood_rejected += 1
            else:
                ood_false_accept += 1

    metrics = {
        "dataset_path": str(dataset_path),
        "loaded_sample_count": len(samples),
        "sampled_size": len(sampled),
        "sampled_split_counts": dict(Counter(sample["split"] for sample in sampled)),
        "candidate_generation_success_rate": round(candidate_success / max(len(sampled), 1), 4),
        "sample_target_ir_exact_match": round(exact_match / max(sum(1 for s in sampled if s["supported"]), 1), 4),
        "eval_seen_target_targetir_exact_match": _split_exact(split_rows["eval_seen_target_unseen_paraphrase"]),
        "eval_unseen_target_targetir_exact_match": _split_exact(split_rows["eval_unseen_target"]),
        "eval_ood_rejection_rate": round(ood_rejected / max(ood_total, 1), 4),
        "eval_ood_false_accept_rate": round(ood_false_accept / max(ood_total, 1), 4),
        "paraphrase_group_consistency_sampled": _group_consistency(records),
        "language_target_unknown_count": sum(1 for sample in sampled if _target_option(sample, "language_target") == "unknown"),
        "true_missing_layer_rate": round(true_missing / max(len(sampled), 1), 4),
        "early_reject_short_path_rate": round(early_reject_short / max(len(sampled), 1), 4),
        "runtime_seconds": round(time.time() - start_time, 4),
    }
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    CANDIDATES_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records),
        encoding="utf-8",
    )
    REPORT_PATH.write_text(_report_markdown(metrics), encoding="utf-8")
    metrics["report_path"] = str(REPORT_PATH)
    metrics["candidates_path"] = str(CANDIDATES_PATH)
    return metrics


def _sample_splits(samples: List[Dict], sample_size: int) -> List[Dict]:
    by_split = defaultdict(list)
    for sample in samples:
        by_split[sample["split"]].append(sample)
    if sample_size >= 800:
        scale = sample_size / 1000
        desired = {
            "train": min(int(400 * scale), len(by_split["train"])),
            "eval_seen_target_unseen_paraphrase": min(int(200 * scale), len(by_split["eval_seen_target_unseen_paraphrase"])),
            "eval_unseen_target": min(int(200 * scale), len(by_split["eval_unseen_target"])),
            "eval_ood": min(sample_size - int(800 * scale), len(by_split["eval_ood"])),
        }
    else:
        quarter = max(1, sample_size // 4)
        desired = {split: min(quarter, len(rows)) for split, rows in by_split.items()}
    result = []
    for split in ["train", "eval_seen_target_unseen_paraphrase", "eval_unseen_target", "eval_ood"]:
        result.extend(by_split[split][: desired.get(split, 0)])
    return result[:sample_size]


def _split_exact(rows: List[Dict]) -> float:
    supported = [row for row in rows if row["supported"]]
    return round(sum(1 for row in supported if row["exact_match"]) / max(len(supported), 1), 4)


def _group_consistency(records: List[Dict]) -> float:
    groups = defaultdict(list)
    for row in records:
        if row["supported"] and row["target_ir_pred"]:
            groups[row["paraphrase_group"]].append(row["target_ir_pred"])
    if not groups:
        return 0.0
    consistent = sum(1 for preds in groups.values() if len(set(preds)) == 1)
    return round(consistent / len(groups), 4)


def _empty_row(sample: Dict) -> Dict:
    return {
        "sample_id": sample["sample_id"],
        "split": sample["split"],
        "input_text": sample["input_text"],
        "input_mode": sample["input_mode"],
        "paraphrase_group": sample["paraphrase_group"],
        "supported": sample["supported"],
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": None,
        "unsupported_pred": False,
        "exact_match": False,
        "expected_output_match": False,
        "early_exit": False,
        "reject_type": "missing_layer",
        "rejected_by_layer": None,
        "decision_count": 0,
        "target_path_length": len(sample.get("target_branch_path", [])),
    }


def _target_option(sample: Dict, layer_name: str):
    for layer, option in sample.get("target_branch_path", []):
        if layer == layer_name:
            return option
    return None


def _report_markdown(metrics: Dict) -> str:
    lines = [
        "# v0.6.8 Scale Smoke Benchmark（规模化冒烟基准） Report",
        "",
        "This is a diagnostic Scale Smoke Benchmark（规模化冒烟基准）, not a convergence or performance claim.",
        "",
        "## Metrics（指标）",
        "",
    ]
    for key in [
        "loaded_sample_count",
        "sampled_size",
        "sampled_split_counts",
        "candidate_generation_success_rate",
        "sample_target_ir_exact_match",
        "eval_seen_target_targetir_exact_match",
        "eval_unseen_target_targetir_exact_match",
        "eval_ood_rejection_rate",
        "eval_ood_false_accept_rate",
        "paraphrase_group_consistency_sampled",
        "language_target_unknown_count",
        "true_missing_layer_rate",
        "early_reject_short_path_rate",
        "runtime_seconds",
    ]:
        lines.append(f"- {key}: {metrics[key]}")
    lines.extend(
        [
            "",
            "## Notes（说明）",
            "",
            "- BranchChain（分支链）, Confidence-Gated Continuation（置信度守卫式继续）, AtomicSynthesis（原子结构合成）, and TargetIR（目标中间表示） are exercised only in a sampled diagnostic path.",
            "- OOD Evaluation（分布外评测）, Seen-Target Evaluation（已见目标评测）, and Unseen-Target Evaluation（未见目标评测） are reported separately where sampled.",
            "",
            "## Non-Claims（非主张）",
            "",
            "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not patch old source code.",
            "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v0.6.8 Scale Smoke Benchmark（规模化冒烟基准）.")
    parser.add_argument("--dataset", type=Path, default=Path("datasets/v0_6_8/jianmu_v0_6_8_all.jsonl"))
    parser.add_argument("--sample-size", type=int, default=800)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--population-per-layer", type=int, default=8)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    metrics = run_smoke_benchmark(args.dataset, args.sample_size, args.seed, args.population_per_layer, args.top_k)
    print(f"loaded sample count: {metrics['loaded_sample_count']}")
    print(f"sampled size: {metrics['sampled_size']}")
    print(f"candidate_generation_success_rate: {metrics['candidate_generation_success_rate']}")
    print(f"sample_target_ir_exact_match: {metrics['sample_target_ir_exact_match']}")
    print(f"eval_seen_target_targetir_exact_match: {metrics['eval_seen_target_targetir_exact_match']}")
    print(f"eval_unseen_target_targetir_exact_match: {metrics['eval_unseen_target_targetir_exact_match']}")
    print(f"eval_ood_rejection_rate: {metrics['eval_ood_rejection_rate']}")
    print(f"eval_ood_false_accept_rate: {metrics['eval_ood_false_accept_rate']}")
    print(f"report path: {metrics['report_path']}")


if __name__ == "__main__":
    main()
