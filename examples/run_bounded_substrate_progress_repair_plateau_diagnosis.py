from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.bounded_substrate_beam_sweep import run_beam_sweep
from jianmu.self_learning.darwinforge.bounded_substrate_candidate_error_taxonomy import run_candidate_error_taxonomy
from jianmu.self_learning.darwinforge.bounded_substrate_plateau_diagnosis import run_ablation_plateau_diagnosis, run_integrity_check, run_stage_plateau_diagnosis
from jianmu.self_learning.darwinforge.bounded_substrate_plateau_readiness import assess_plateau_readiness
from jianmu.self_learning.darwinforge.bounded_substrate_progress_repair import run_progress_sanity


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-records", default="records/v0_9_8")
    parser.add_argument("--baseline-records", default="records/v0_9_7")
    parser.add_argument("--dataset-dir", default="datasets/v0_9_6_turing_substrate_curriculum")
    parser.add_argument("--output-records", default="records/v0_9_8_1")
    parser.add_argument("--modes", default="progress-sanity")
    parser.add_argument("--beam-sizes", default="4,8,16,32")
    parser.add_argument("--heldout-samples", type=int, default=2000)
    parser.add_argument("--boundary-samples", type=int, default=2000)
    parser.add_argument("--progress", default="true")
    parser.add_argument("--progress-interval-seconds", type=float, default=2.0)
    parser.add_argument("--progress-min-samples", type=int, default=100)
    parser.add_argument("--force-text-progress", default="true")
    parser.add_argument("--seed", type=int, default=66)
    args = parser.parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    modes = {part.strip() for part in args.modes.split(",") if part.strip()}
    progress = run_progress_sanity(out, args.progress.lower() == "true", args.progress_interval_seconds, args.progress_min_samples, args.force_text_progress.lower() == "true")
    taxonomy = run_candidate_error_taxonomy(args.source_records, out) if "plateau-diagnosis" in modes or "progress-sanity" in modes else {}
    beam = run_beam_sweep(args.dataset_dir, args.source_records, out, [int(part) for part in args.beam_sizes.split(",") if part.strip()], args.heldout_samples, args.boundary_samples, args.seed) if "beam-sweep" in modes else {}
    ablation = run_ablation_plateau_diagnosis(args.source_records, out) if "ablation-diagnosis" in modes else {}
    stage = run_stage_plateau_diagnosis(args.source_records, args.baseline_records, out) if "stage-diagnosis" in modes else {}
    integrity = run_integrity_check(args.source_records, out) if "integrity-check" in modes or "progress-sanity" in modes else {}
    readiness = assess_plateau_readiness(progress, taxonomy, beam, ablation, stage, integrity, out)
    _write_mainline(out, progress, taxonomy, beam, ablation, stage, integrity, readiness)
    print(json.dumps({
        "progress_events_emitted": progress.get("progress_events_emitted"),
        "dominant_plateau_cause": readiness.get("dominant_plateau_cause"),
        "recommended_claim_level": readiness.get("recommended_claim_level"),
    }, ensure_ascii=False, indent=2, sort_keys=True))


def _write_mainline(out: Path, progress: dict, taxonomy: dict, beam: dict, ablation: dict, stage: dict, integrity: dict, readiness: dict) -> None:
    conclusion = {
        "what_this_version_proved": "progress reporting was repaired as an observation tool and v0.9.8 plateau causes were diagnosed from existing records",
        "what_this_version_did_not_prove": ["Turing completeness", "solved arithmetic", "solved program synthesis", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
        "progress_previous_issue": "v0.9.8 emitted only phase-boundary progress events, so long phases had little visible progress",
        "progress_repaired": readiness.get("progress_repair_completed"),
        "progress_events_emitted": progress.get("progress_events_emitted"),
        "progress_affects_metrics": not progress.get("progress_metrics_safe", False),
        "dominant_plateau_cause": readiness.get("dominant_plateau_cause"),
        "candidate_miss_rate": taxonomy.get("candidate_miss_rate"),
        "in_beam_wrong_top1_rate": taxonomy.get("in_beam_wrong_top1_rate"),
        "beam_sweep_conclusion": {
            "beam_bottleneck_likely": beam.get("beam_bottleneck_likely"),
            "ranking_bottleneck_likely": beam.get("ranking_bottleneck_likely"),
            "generation_bottleneck_likely": beam.get("generation_bottleneck_likely"),
        },
        "ablation_diagnosis": {
            "root_colony_gain_present": ablation.get("root_colony_gain_present"),
            "nutrient_toxic_gain_present": ablation.get("nutrient_toxic_gain_present"),
            "lifecycle_gain_present": ablation.get("lifecycle_gain_present"),
        },
        "stage_plateau": {
            "weakest_stages": stage.get("weakest_stages", []),
            "stages_improved": stage.get("stages_improved", []),
            "stages_flat": stage.get("stages_flat", []),
            "stages_regressed": stage.get("stages_regressed", []),
        },
        "integrity_check_passed": integrity.get("integrity_check_passed"),
        "recommended_next_action": readiness.get("recommended_next_action"),
        "recommended_claim_level": readiness.get("recommended_claim_level"),
        "blocking_issues": readiness.get("blocking_issues", []),
        "required_next_run": readiness.get("required_next_run"),
        "paper_v2_candidate_results": ["progress safety", "plateau diagnosis", "beam sweep diagnostic"],
        "post_v1_reserved_routes": ["root similarity incremental training", "verified backend as teacher for NL-to-semantic-IR adapter"],
        "must_revalidate": ["diagnostic sweep conclusions on a fresh run"],
        "still_not_proven": ["Turing completeness", "solved arithmetic", "solved program synthesis", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
    }
    (out / "mainline_conclusion.json").write_text(json.dumps(conclusion, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# v0.9.8.1 Mainline Conclusion",
        "",
        f"Recommended claim level: {readiness.get('recommended_claim_level')}",
        f"Dominant plateau cause: {readiness.get('dominant_plateau_cause')}",
        f"Progress events emitted: {progress.get('progress_events_emitted')}",
        "",
        "Still not proven: Turing completeness, solved arithmetic, solved program synthesis, stable convergence, solved OOD, general program synthesis, same-size LLM advantage, safe real promotion, production readiness.",
    ]
    (out / "mainline_conclusion.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

