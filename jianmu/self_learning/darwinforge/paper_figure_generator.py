from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List


FIGURES = [
    "fig_scale_signal",
    "fig_boundary_metrics",
    "fig_ood_taxonomy",
    "fig_persistence_progression",
    "fig_external_ood_multiseed",
    "fig_pipeline_overview",
]


def generate_paper_figures(figure_data_dir: str | Path, records_figure_dir: str | Path, paper_assets_dir: str | Path) -> Dict[str, Any]:
    data_dir = Path(figure_data_dir)
    records_dir = Path(records_figure_dir)
    assets_dir = Path(paper_assets_dir)
    records_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Dict[str, str]] = []
    matplotlib_available = True
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except (ImportError, ModuleNotFoundError):
        matplotlib_available = False
        plt = None

    if matplotlib_available:
        _plot_scale_signal(plt, data_dir, records_dir)
        _plot_boundary_metrics(plt, data_dir, records_dir)
        _plot_ood_taxonomy(plt, data_dir, records_dir)
        _plot_persistence(plt, data_dir, records_dir)
        _plot_multiseed(plt, data_dir, records_dir)
        _plot_pipeline(plt, records_dir)
    else:
        for stem in FIGURES:
            _write_placeholder(records_dir / f"{stem}.png", f"{stem}: matplotlib unavailable")
            _write_placeholder(records_dir / f"{stem}.pdf", f"{stem}: matplotlib unavailable")
    for stem in FIGURES:
        for ext in ["png", "pdf"]:
            src = records_dir / f"{stem}.{ext}"
            if src.exists():
                dst = assets_dir / src.name
                shutil.copyfile(src, dst)
                outputs.append({"figure": stem, "records_path": str(src), "paper_assets_path": str(dst), "format": ext})
    manifest = {"paper_figures_generated": True, "matplotlib_available": matplotlib_available, "figures": outputs}
    (records_dir / "figure_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (assets_dir / "figure_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _plot_scale_signal(plt, data_dir: Path, out: Path) -> None:
    rows = _read_csv(data_dir / "scale_signal.csv")
    x = [row["mode"] for row in rows]
    beam = [_num(row.get("global_correct_targetir_in_beam_rate")) for row in rows]
    failure = [_num(row.get("candidate_space_failure_rate")) for row in rows]
    plt.figure(figsize=(6, 4))
    if any(v is not None for v in beam + failure):
        plt.plot(x, [v if v is not None else 0 for v in beam], marker="o", label="global beam")
        plt.plot(x, [v if v is not None else 0 for v in failure], marker="s", label="candidate failure")
        plt.legend()
    else:
        plt.text(0.5, 0.5, "data missing", ha="center", va="center")
    plt.title("Scale Signal")
    plt.ylabel("rate")
    plt.xticks(rotation=20)
    _save(plt, out / "fig_scale_signal")


def _plot_boundary_metrics(plt, data_dir: Path, out: Path) -> None:
    rows = _read_csv(data_dir / "boundary_before_after.csv")
    labels = [row["metric"] for row in rows]
    before = [_num(row.get("before")) or 0 for row in rows]
    after = [_num(row.get("after")) or 0 for row in rows]
    xs = range(len(labels))
    plt.figure(figsize=(7, 4))
    plt.bar([x - 0.18 for x in xs], before, width=0.35, label="before")
    plt.bar([x + 0.18 for x in xs], after, width=0.35, label="after")
    plt.title("Boundary Metrics")
    plt.ylabel("rate")
    plt.xticks(list(xs), labels, rotation=25, ha="right")
    plt.legend()
    _save(plt, out / "fig_boundary_metrics")


def _plot_ood_taxonomy(plt, data_dir: Path, out: Path) -> None:
    rows = _read_csv(data_dir / "ood_taxonomy.csv")
    labels = [row.get("class", "missing") for row in rows]
    counts = [_num(row.get("count")) or 0 for row in rows]
    plt.figure(figsize=(6, 4))
    if sum(counts) > 0:
        plt.bar(labels, counts)
    else:
        plt.text(0.5, 0.5, "data missing", ha="center", va="center")
    plt.title("OOD Taxonomy")
    plt.ylabel("count")
    plt.xticks(rotation=25, ha="right")
    _save(plt, out / "fig_ood_taxonomy")


def _plot_persistence(plt, data_dir: Path, out: Path) -> None:
    rows = _read_csv(data_dir / "persistence_progression.csv")
    levels = {"summary_only": 1, "partial": 2, "full_router_root": 3}
    x = [row.get("version", "") for row in rows]
    y = [levels.get(row.get("support_level"), 0) for row in rows]
    plt.figure(figsize=(6, 4))
    plt.plot(x, y, marker="o")
    plt.yticks([0, 1, 2, 3], ["missing", "summary", "partial", "full"])
    plt.title("Persistence Progression")
    _save(plt, out / "fig_persistence_progression")


def _plot_multiseed(plt, data_dir: Path, out: Path) -> None:
    rows = [row for row in _read_csv(data_dir / "external_ood_multiseed.csv") if row.get("version") == "v0.9.0"]
    x = [str(row.get("seed")) for row in rows if row.get("seed") != "missing"]
    y = [_num(row.get("external_ood_false_accept")) or 0 for row in rows if row.get("seed") != "missing"]
    plt.figure(figsize=(6, 4))
    if x:
        plt.bar(x, y)
    else:
        plt.text(0.5, 0.5, "data missing", ha="center", va="center")
    plt.title("External OOD Multi-Seed")
    plt.ylabel("false accept rate")
    plt.xlabel("seed")
    _save(plt, out / "fig_external_ood_multiseed")


def _plot_pipeline(plt, out: Path) -> None:
    plt.figure(figsize=(8, 2.8))
    labels = ["input", "canonicalizer", "BranchChain", "Root Colony", "free-beam/compiler", "boundary decision"]
    for idx, label in enumerate(labels):
        plt.gca().add_patch(plt.Rectangle((idx, 0.4), 0.85, 0.4, fill=False))
        plt.text(idx + 0.425, 0.6, label, ha="center", va="center", fontsize=8)
        if idx < len(labels) - 1:
            plt.arrow(idx + 0.86, 0.6, 0.25, 0, head_width=0.05, length_includes_head=True)
    plt.xlim(-0.1, len(labels))
    plt.ylim(0, 1.2)
    plt.axis("off")
    plt.title("Pipeline Overview")
    _save(plt, out / "fig_pipeline_overview")


def _save(plt, stem: Path) -> None:
    plt.tight_layout()
    plt.savefig(stem.with_suffix(".png"), dpi=160)
    plt.savefig(stem.with_suffix(".pdf"))
    plt.close()


def _read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _num(value: Any) -> float | None:
    try:
        if value in {None, "", "missing"}:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _write_placeholder(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".png":
        # Minimal valid 1x1 transparent PNG. The manifest records why this placeholder exists.
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
    else:
        safe = text.replace("(", "[").replace(")", "]")
        path.write_bytes(f"%PDF-1.4\n1 0 obj<<>>endobj\n2 0 obj<< /Length {len(safe)+32} >>stream\nBT /F1 12 Tf 40 700 Td ({safe}) Tj ET\nendstream endobj\ntrailer<<>>\n%%EOF\n".encode("latin-1", errors="replace"))
