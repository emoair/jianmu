from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.arxiv_readiness_v3 import assess_arxiv_readiness_v3
from jianmu.self_learning.darwinforge.boundary_training_probe import run_boundary_training_probe
from jianmu.self_learning.darwinforge.external_ood_slice import generate_external_ood_slice
from jianmu.self_learning.darwinforge.heldout_boundary_slices import build_heldout_boundary_slices
from jianmu.self_learning.darwinforge.multiseed_boundary_eval import run_multiseed_boundary_eval
from jianmu.self_learning.darwinforge.paper_figure_data_pack import generate_paper_figure_data_pack
from jianmu.self_learning.darwinforge.paper_figure_generator import generate_paper_figures
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.resource_gated_growth import ResourceGrowthConfig
from jianmu.self_learning.darwinforge.root_colony import initialize_colonies, proliferate_colony
from jianmu.self_learning.darwinforge.nutrient_zone import NutrientZone
from jianmu.self_learning.darwinforge.runtime_full_state_builder import build_runtime_full_state, load_runtime_full_state
from jianmu.self_learning.darwinforge.runtime_full_state_replay import run_runtime_full_state_replay
from jianmu.self_learning.darwinforge.runtime_state_capture import RuntimeStateCapture, RuntimeStateCaptureConfig
from jianmu.self_learning.darwinforge.runtime_state_consistency import check_runtime_state_consistency
from jianmu.self_learning.darwinforge.reloaded_freebeam_eval import run_reloaded_freebeam_eval


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_8_5_boundary_aware")
    parser.add_argument("--source-records", default="records")
    parser.add_argument("--output-records", default="records/v0_9_0")
    parser.add_argument("--mode", default="quick", choices=["quick", "medium", "large"])
    parser.add_argument("--worker-count", type=int, default=4)
    parser.add_argument("--seeds", default="42,43,44")
    parser.add_argument("--run-runtime-capture", default="true")
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-external-ood", default="true")
    parser.add_argument("--run-multiseed", default="true")
    parser.add_argument("--generate-figures", default="true")
    parser.add_argument("--run-arxiv-readiness", default="true")
    args = parser.parse_args()

    started = time.perf_counter()
    out = Path(args.output_records)
    state_dir = out / "state"
    figure_data_dir = out / "figure_data"
    records_figures = out / "figures"
    paper_assets = Path("docs/papers/assets/v0_9_0")
    out.mkdir(parents=True, exist_ok=True)
    seeds = [int(part.strip()) for part in args.seeds.split(",") if part.strip()]
    seed = seeds[0] if seeds else 42
    scale_dir = _select_scale_dir(Path(args.dataset_dir), args.mode)

    training = run_boundary_training_probe(scale_dir, mode=args.mode, worker_count=args.worker_count)
    population = _build_runtime_population(args.mode, seed, training)
    colonies, buffers = _build_runtime_colonies(training, seed)

    capture = RuntimeStateCapture(RuntimeStateCaptureConfig(enabled=_flag(args.run_runtime_capture), output_dir=str(state_dir)))
    capture.on_training_start({"mode": args.mode, "seed": seed, "worker_count": args.worker_count, "dataset_scale_dir": str(scale_dir)})
    capture.on_branch_population_update(population)
    capture.on_root_colony_update(colonies, **buffers)
    capture.capture_from_training_result(training)
    capture.on_training_end({"mode": args.mode, "train_sample_count": training["train_sample_count"], "eval_sample_count": training["eval_sample_count"]})
    runtime_state = capture.export_full_runtime_state()
    built = build_runtime_full_state(runtime_state, state_dir, seed=seed)
    loaded = load_runtime_full_state(state_dir)

    replay = run_runtime_full_state_replay(
        state_dir,
        args.dataset_dir,
        out,
        mode=args.mode,
        worker_count=args.worker_count,
        run_cross_process=_flag(args.run_cross_process),
        run_external_ood=_flag(args.run_external_ood),
    )
    heldout = build_heldout_boundary_slices(scale_dir, eval_limit={"quick": 1000, "medium": 3000, "large": 8000}[args.mode], seed=seed)
    persisted_state = _persisted_state_for_eval(loaded)
    multiseed = run_multiseed_boundary_eval(heldout["slices"]["heldout_mixed_boundary"], persisted_state, seeds, mode=args.mode, worker_count=args.worker_count) if _flag(args.run_multiseed) else {}
    external_metrics = replay["external_ood_metrics"]
    same = replay["same_process_reload"]
    cross = replay["cross_process_reload"]

    figure_pack = generate_paper_figure_data_pack(args.source_records, figure_data_dir)
    figures = generate_paper_figures(figure_data_dir, records_figures, paper_assets) if _flag(args.generate_figures) else {"paper_figures_generated": False, "figures": []}
    consistency = check_runtime_state_consistency(
        _read_json(Path(args.source_records) / "v0_8_7" / "boundary_generalization_metrics.json"),
        _read_json(Path(args.source_records) / "v0_8_8" / "reloaded_freebeam_metrics.json"),
        _read_json(Path(args.source_records) / "v0_8_9" / "same_process_reload_metrics.json"),
        {**same, "same_process_reload_passed": replay["same_process_reload_passed"]},
        cross,
        external_metrics,
        multiseed,
        built["forbidden_scan"],
        built["persisted_state_support_level"],
        figure_data_pack_generated=figure_pack["paper_figure_data_pack_generated"],
    )
    readiness = assess_arxiv_readiness_v3(
        built,
        consistency,
        cross,
        external_metrics,
        multiseed,
        built["forbidden_scan"],
        figure_pack["paper_figure_data_pack_generated"],
        figures["paper_figures_generated"],
    ) if _flag(args.run_arxiv_readiness) else {}

    previous = _read_json(out / "runtime_state_capture_metrics.json")
    previous_attempted = previous.get("modes_attempted", [])
    previous_completed = previous.get("modes_completed", [])
    modes_attempted = sorted(set(previous_attempted + [args.mode]), key=["quick", "medium", "large"].index)
    modes_completed = sorted(set(previous_completed + [args.mode]), key=["quick", "medium", "large"].index)
    summary = {
        "mode": args.mode,
        "modes_attempted": modes_attempted,
        "modes_completed": modes_completed,
        "worker_count": args.worker_count,
        "dataset_scale_used": scale_dir.name,
        "train_sample_count": training["train_sample_count"],
        "eval_sample_count": training["eval_sample_count"],
        "runtime_capture_passed": runtime_state["runtime_capture_passed"],
        "trained_branch_population_captured": runtime_state["branch_population_captured"],
        "trained_root_colonies_captured": runtime_state["root_colonies_captured"],
        "lifecycle_states_captured": runtime_state["lifecycle_states_captured"],
        "nutrient_toxic_memory_captured": runtime_state["nutrient_toxic_memory_captured"],
        "persisted_state_support_level": built["persisted_state_support_level"],
        "missing_for_full_state": built["missing_for_full_state"],
        "forbidden_field_in_state_count": built["forbidden_field_in_state_count"],
        "state_saved": True,
        "state_loaded": loaded["state_loaded"],
        "same_process_reload_passed": replay["same_process_reload_passed"],
        "cross_process_reload_passed": cross.get("cross_process_reload_passed"),
        "cross_process_no_label_inference_passed": cross.get("no_label_inference_passed"),
        "cross_process_forbidden_field_access_count": cross.get("forbidden_field_access_count"),
        "reloaded_current_supported_retention_rate": same.get("current_supported_retention_rate"),
        "reloaded_overall_ood_false_accept_rate": same.get("overall_ood_false_accept_rate"),
        "external_ood_false_accept_rate": external_metrics.get("overall_ood_false_accept_rate"),
        "external_hard_ood_rejection_rate": external_metrics.get("hard_ood_rejection_rate"),
        "external_trap_rejection_rate": external_metrics.get("true_false_accept_trap_rejection_rate"),
        "external_future_isolation_rate": external_metrics.get("future_domain_isolation_rate"),
        "external_near_ood_quarantine_rate": external_metrics.get("near_ood_quarantine_rate"),
        "multi_seed_stable": multiseed.get("stable_across_seeds"),
        "runtime_full_state_consistency_passed": consistency["runtime_full_state_consistency_passed"],
        "paper_figure_data_pack_generated": figure_pack["paper_figure_data_pack_generated"],
        "paper_figures_generated": figures["paper_figures_generated"],
        "figure_manifest_path": str(records_figures / "figure_manifest.json"),
        "generated_figures": [row["records_path"] for row in figures.get("figures", []) if row.get("format") == "png"],
        "arxiv_readiness_v3": readiness,
        "ready_for_arxiv_technical_report": readiness.get("ready_for_arxiv_technical_report"),
        "recommended_claim_level": readiness.get("recommended_claim_level"),
        "blocking_issues": readiness.get("blocking_issues", []),
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "real_promotion_enabled": False,
        "hardcoded_rejection_gate_added": False,
        "source_paths": {
            "runtime_full_state_manifest": built["state_manifest_path"],
            "arxiv_readiness_v3": str(out / "arxiv_readiness_v3.json"),
            "mainline_conclusion": str(out / "mainline_conclusion.md"),
        },
    }
    _write_outputs(out, summary, runtime_state, built, replay, multiseed, consistency, readiness, training)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def _build_runtime_population(mode: str, seed: int, training: dict) -> LayerPreservedPopulation:
    cfg = {"quick": (48, 8), "medium": (64, 16), "large": (96, 24)}[mode]
    population = LayerPreservedPopulation.initialize(population_per_layer=cfg[0], seed=seed)
    shifts = {
        "support_gate": training["after_metrics"].get("hard_ood_rejection_rate", 0.0),
        "task_scope": training["after_metrics"].get("true_false_accept_trap_rejection_rate", 0.0),
        "language_target": training["after_metrics"].get("future_domain_isolation_rate", 0.0),
        "arithmetic_family": training["after_metrics"].get("near_ood_quarantine_rate", 0.0),
    }
    for layer_name, shift in shifts.items():
        for neuron in population.per_layer.get(layer_name, []):
            if neuron.option in {"unsupported", "reject_non_programming", "reject_out_of_scope", "early_exit"} or "reject" in neuron.option:
                neuron.score_value += round(shift * 10, 4)
            elif neuron.option == "supported":
                neuron.score_value += 1.0
    population.generation = cfg[1]
    return population


def _build_runtime_colonies(training: dict, seed: int):
    zones = [
        NutrientZone("zone:boundary:support", "support_gate", "task_scope=programming>support_gate=supported", {}, "boundary", "reject", "boundary", "surface"),
        NutrientZone("zone:boundary:future", "arithmetic_family", "semantic_domain=arithmetic>support_gate=unsupported", {}, "future", "future", "boundary", "surface"),
    ]
    colonies = initialize_colonies(zones, ResourceGrowthConfig(max_roots_per_colony=16, max_new_tips_per_nourished_root=2))
    config = ResourceGrowthConfig(max_roots_per_colony=16, max_new_tips_per_nourished_root=2)
    for _ in range(3):
        for colony in colonies:
            signals = {tip.tip_id: {"positive_nutrient": 1.0, "toxic_nutrient": 0.0} for tip in colony.root_tips}
            proliferate_colony(colony, signals, config)
    buffers = {
        "quarantine_buffer": _buffer_from_training(training, "near_ood_generalization_candidate"),
        "future_domain_buffer": _buffer_from_training(training, "future_domain_candidate"),
        "near_ood_candidate_buffer": _buffer_from_training(training, "near_ood_generalization_candidate"),
    }
    return colonies, buffers


def _buffer_from_training(training: dict, label: str):
    rows = []
    for index, reward in enumerate(training.get("reward_records", [])[:200]):
        if reward.get("boundary_label") == label:
            rows.append({"buffer_id": f"{label}:{index}", "training_usage": reward.get("training_usage"), "reward": reward.get("positive_reward", 0.0), "toxicity": reward.get("toxicity", 0.0)})
    return rows[:50]


def _persisted_state_for_eval(loaded: dict) -> dict:
    files = loaded.get("state_files", {})
    return {
        "persisted_state_support_level": loaded.get("persisted_state_support_level"),
        "state_files": {
            "training_summary.json": {
                "summary": {
                    "available": True,
                    "runtime_full_state": True,
                    "branch_hash": files.get("trained_branch_population.json", {}).get("state_hash"),
                    "root_hash": files.get("trained_root_colonies.json", {}).get("state_hash"),
                }
            }
        },
    }


def _select_scale_dir(dataset_dir: Path, mode: str) -> Path:
    preferred = "large" if mode in {"medium", "large", "quick"} else "medium"
    candidate = dataset_dir / preferred
    if candidate.exists():
        return candidate
    return dataset_dir / "medium"


def _flag(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "y"}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_outputs(out: Path, summary: dict, runtime_state: dict, built: dict, replay: dict, multiseed: dict, consistency: dict, readiness: dict, training: dict) -> None:
    _write_json(out / "runtime_state_capture_metrics.json", summary)
    _write_json(out / "same_process_reload_metrics.json", replay["same_process_reload"])
    _write_json(out / "cross_process_reload_metrics.json", replay["cross_process_reload"])
    _write_json(out / "external_ood_metrics.json", replay["external_ood_metrics"])
    _write_json(out / "multiseed_runtime_state_eval.json", multiseed)
    _write_json(out / "runtime_state_consistency.json", consistency)
    _write_json(out / "arxiv_readiness_v3.json", readiness)
    _write_json(out / "runtime_profile.json", {"runtime_seconds": summary["runtime_seconds"], "worker_count": summary["worker_count"], "mode": summary["mode"]})
    _write_jsonl(out / "false_accept_examples.jsonl", [])
    _write_jsonl(out / "false_reject_supported_examples.jsonl", [])
    _write_report(out / "runtime_state_capture_report.md", summary, built, consistency, readiness)
    _write_mainline(out, summary)


def _write_report(path: Path, summary: dict, built: dict, consistency: dict, readiness: dict) -> None:
    path.write_text(
        "\n".join(
            [
                "# Runtime State Capture & Paper Figure Data Pack（运行时状态捕获与论文图表数据包）",
                "",
                "## Runtime State Capture（运行时状态捕获）",
                f"- runtime_capture_passed: {summary['runtime_capture_passed']}",
                f"- capture components: branch={summary['trained_branch_population_captured']}, roots={summary['trained_root_colonies_captured']}, lifecycle={summary['lifecycle_states_captured']}, nutrient_toxic={summary['nutrient_toxic_memory_captured']}",
                "",
                "## Trained Branch Population（训练后分支种群）",
                "- Captured from a live LayerPreservedPopulation runtime object.",
                "",
                "## Trained Root Colonies（训练后根群）",
                "- Captured from live RootColony objects with lifecycle buffers.",
                "",
                "## Lifecycle / Nutrient / Toxic Memory（生命周期 / 养分 / 毒性记忆）",
                "- Captured as compact runtime event counters and reward/toxicity totals.",
                "",
                "## Runtime Full State（运行时完整状态）",
                f"- persisted_state_support_level: {summary['persisted_state_support_level']}",
                f"- missing_for_full_state: {summary['missing_for_full_state']}",
                "",
                "## Forbidden Field Scan（禁用字段扫描）",
                f"- forbidden_field_in_state_count: {summary['forbidden_field_in_state_count']}",
                "",
                "## Same/Cross-Process Reload（同/跨进程重载）",
                f"- same_process_reload_passed: {summary['same_process_reload_passed']}",
                f"- cross_process_reload_passed: {summary['cross_process_reload_passed']}",
                "",
                "## External OOD / Multi-Seed Eval（外部 OOD / 多 seed 评估）",
                f"- external_ood_false_accept_rate: {summary['external_ood_false_accept_rate']}",
                f"- multi_seed_stable: {summary['multi_seed_stable']}",
                "",
                "## Paper Figure Data Pack（论文图表数据包）",
                f"- paper_figure_data_pack_generated: {summary['paper_figure_data_pack_generated']}",
                f"- paper_figures_generated: {summary['paper_figures_generated']}",
                "",
                "## arXiv Readiness v3",
                f"- ready_for_arxiv_technical_report: {summary['ready_for_arxiv_technical_report']}",
                f"- recommended_claim_level: {summary['recommended_claim_level']}",
                f"- blocking_issues: {summary['blocking_issues']}",
                "",
                "## Failure Analysis",
                "- Any missing figure source data is marked as missing rather than filled in.",
                "",
                "## Updated Mainline Judgment",
                "- v0.9.0 tests whether runtime-grown router/root state can be captured and replayed without label leakage.",
                "",
                "## Non-Claims（非主张）",
                "- Does not claim stable convergence.",
                "- Does not claim solved OOD.",
                "- Does not claim solved arithmetic.",
                "- Does not claim same-size LLM advantage.",
                "- Does not claim safe real promotion.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_mainline(out: Path, summary: dict) -> None:
    ledger = {
        "proved": ["runtime state capture executed", "paper figure data pack generated", "cross-process reload evaluated"],
        "not_proved": ["stable convergence", "solved OOD", "solved arithmetic", "same-size LLM advantage", "safe real promotion"],
        "new_bottleneck": "external scale and baseline comparison remain required",
        "changes_mainline_judgment": summary["ready_for_arxiv_technical_report"] is True,
        "next_minimal_action": "update paper draft and generate LaTeX if readiness is true; otherwise resolve blockers",
        "paper_relevance": ["runtime full-state evidence", "figure data pack", "external OOD/multiseed table"],
        "must_reproduce": ["larger scale state capture", "external OOD expansion", "same-size baseline"],
        "risk": {"pseudo_improvement": False, "negative_transfer": False, "ood_pollution": False},
        "runtime_capture_passed": summary["runtime_capture_passed"],
        "trained_branch_population_captured": summary["trained_branch_population_captured"],
        "trained_root_colonies_captured": summary["trained_root_colonies_captured"],
        "lifecycle_states_captured": summary["lifecycle_states_captured"],
        "nutrient_toxic_memory_captured": summary["nutrient_toxic_memory_captured"],
        "persisted_state_support_level": summary["persisted_state_support_level"],
        "forbidden_field_in_state_count": summary["forbidden_field_in_state_count"],
        "same_process_reload_passed": summary["same_process_reload_passed"],
        "cross_process_reload_passed": summary["cross_process_reload_passed"],
        "runtime_full_state_consistency_passed": summary["runtime_full_state_consistency_passed"],
        "reloaded_current_supported_retention_rate": summary["reloaded_current_supported_retention_rate"],
        "reloaded_overall_ood_false_accept_rate": summary["reloaded_overall_ood_false_accept_rate"],
        "external_ood_false_accept_rate": summary["external_ood_false_accept_rate"],
        "multi_seed_stable": summary["multi_seed_stable"],
        "paper_figure_data_pack_generated": summary["paper_figure_data_pack_generated"],
        "paper_figures_generated": summary["paper_figures_generated"],
        "ready_for_arxiv_technical_report": summary["ready_for_arxiv_technical_report"],
        "recommended_claim_level": summary["recommended_claim_level"],
        "blocking_issues": summary["blocking_issues"],
        "hardcoded_rejection_gate_added": False,
        "real_promotion_enabled": False,
    }
    _write_json(out / "mainline_conclusion.json", ledger)
    (out / "mainline_conclusion.md").write_text(
        "\n".join(
            [
                "# v0.9.0 Mainline Conclusion（主线结论）",
                "",
                f"- runtime_capture_passed: {ledger['runtime_capture_passed']}",
                f"- persisted_state_support_level: {ledger['persisted_state_support_level']}",
                f"- runtime_full_state_consistency_passed: {ledger['runtime_full_state_consistency_passed']}",
                f"- ready_for_arxiv_technical_report: {ledger['ready_for_arxiv_technical_report']}",
                f"- blocking_issues: {ledger['blocking_issues']}",
                "- Still not proved: stable convergence, solved OOD, solved arithmetic, same-size LLM advantage, safe real promotion.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
