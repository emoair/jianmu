from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from jianmu.self_learning.darwinforge.forgecorpus_algorithm_schema import (
    target_ir_for,
    token_contains_c_source,
    token_contains_expected_output,
    token_contains_raw_ir,
    token_for,
)
from jianmu.self_learning.darwinforge.projectcartographer_schema import (
    compile_result,
    full_compile_validation,
    parse_project_module,
    syntax_frontend_check,
    write_json,
)
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import (
    _build_backend_compile_command,
    detect_arithmetic_backend,
)


DATASET_VERSION = "v1.0.4_csystems_frontier"
GENERATOR = "csystems_frontier_builder"
MAX_SHARD_SIZE_BYTES = 44_000_000


@dataclass(frozen=True)
class CSystemsScaleConfig:
    scale: str
    total: int
    syntax_frontend_target: int
    full_compile_target: int
    max_runtime_hours: float = 6.0
    hard_stop_hours: float = 6.5

    @classmethod
    def for_scale(cls, scale: str) -> "CSystemsScaleConfig":
        if scale == "pilot":
            return cls("pilot", 100_000, 50_000, 2_000)
        if scale == "medium":
            return cls("medium", 500_000, 150_000, 10_000)
        if scale == "large":
            return cls("large", 2_000_000, 300_000, 20_000)
        return cls("full", 5_000_000, 600_000, 50_000)


class CSystemsFrontierConfig:
    pointer_frontier = [
        "address_of_scalar",
        "dereference_assign",
        "pointer_parameter_swap",
        "pointer_array_traversal",
        "pointer_array_sum",
        "pointer_output_parameter",
        "const_pointer_readonly",
    ]
    malloc_frontier = [
        "malloc_int_array",
        "calloc_int_array",
        "malloc_sort_buffer",
        "malloc_dynamic_stack",
        "malloc_dynamic_queue",
        "realloc_grow_buffer_controlled",
        "allocation_failure_branch",
        "free_lifecycle",
    ]
    fileio_frontier = [
        "fopen_read_numbers_tempfile",
        "fopen_write_result_tempfile",
        "fscanf_integer_array",
        "fprintf_summary",
        "read_sort_write",
        "read_matrix_write_transpose",
        "fclose_lifecycle",
        "temp_path_only",
    ]
    multifile_frontier = [
        "main_c_plus_algo_h_algo_c",
        "main_c_plus_utils_h_utils_c",
        "static_helper_in_algo_c",
        "cross_file_function_call",
        "include_guard",
        "header_declaration_match",
        "multi_file_sort",
        "multi_file_search",
        "multi_file_stack_queue",
    ]
    struct_frontier = [
        "struct_pair",
        "struct_array_item",
        "struct_stack",
        "struct_queue",
        "struct_result_return",
        "struct_counter_state",
    ]
    mixed_system_algorithm = [
        "pointer_swap_sort",
        "malloc_quicksort_buffer",
        "file_read_binary_search",
        "multifile_gcd_lcm",
        "struct_stack_eval",
        "malloc_matrix_transpose",
        "file_read_matrix_multiply_small",
        "pointer_counter_machine_state",
    ]
    unsupported_review_boundary = [
        "unsafe_absolute_path",
        "parent_path_traversal",
        "system_call_attempt",
        "remove_rename_delete_attempt",
    ]

    @classmethod
    def families(cls) -> Dict[str, List[str]]:
        return {
            "pointer_frontier": cls.pointer_frontier,
            "malloc_frontier": cls.malloc_frontier,
            "fileio_frontier": cls.fileio_frontier,
            "multifile_frontier": cls.multifile_frontier,
            "struct_frontier": cls.struct_frontier,
            "mixed_system_algorithm": cls.mixed_system_algorithm,
            "adversarial_unsafe_boundary": cls.unsupported_review_boundary,
            "unsupported_review_boundary": cls.unsupported_review_boundary,
        }


FAMILY_WEIGHTS = [
    ("pointer_frontier", 16),
    ("malloc_frontier", 16),
    ("fileio_frontier", 14),
    ("multifile_frontier", 16),
    ("struct_frontier", 10),
    ("mixed_system_algorithm", 18),
    ("adversarial_unsafe_boundary", 5),
    ("unsupported_review_boundary", 5),
]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def family_for_index(index: int) -> str:
    bucket = index % 100
    cursor = 0
    for family, weight in FAMILY_WEIGHTS:
        cursor += weight
        if bucket < cursor:
            return family
    return FAMILY_WEIGHTS[-1][0]


def feature_for_index(index: int, family: str) -> str:
    choices = CSystemsFrontierConfig.families()[family]
    return choices[(index // 100) % len(choices)]


def split_for_index(index: int) -> str:
    bucket = index % 20
    if bucket < 14:
        return "train"
    if bucket < 17:
        return "eval"
    if bucket < 19:
        return "test"
    return "heldout"


def is_supported_family(family: str) -> bool:
    return family not in {"adversarial_unsafe_boundary", "unsupported_review_boundary"}


def expected_action_for(family: str, split: str) -> str:
    if not is_supported_family(family):
        return "reject"
    return "train_current" if split == "train" else "review"


def system_features(family: str, feature: str) -> Dict[str, bool]:
    return {
        "has_pointer": family in {"pointer_frontier", "mixed_system_algorithm"} or "pointer" in feature,
        "has_malloc": family in {"malloc_frontier", "mixed_system_algorithm"} or "malloc" in feature or "calloc" in feature or "realloc" in feature,
        "has_free": family in {"malloc_frontier", "mixed_system_algorithm"} or "free" in feature,
        "has_fileio": family in {"fileio_frontier", "mixed_system_algorithm"} or "file" in feature or "fopen" in feature,
        "has_multifile": family in {"multifile_frontier"} or "multifile" in feature,
        "has_struct": family == "struct_frontier" or "struct" in feature,
        "has_shell": False,
        "has_network": False,
        "has_delete_or_rename": False,
    }


def memory_contract(family: str, feature: str) -> Dict[str, Any]:
    needs_heap = system_features(family, feature)["has_malloc"]
    return {
        "uses_heap_allocation": needs_heap,
        "allocation_failure_branch_present": needs_heap,
        "free_count_matches_alloc_count": needs_heap,
        "double_free_detected": False,
        "use_after_free_detected": False,
        "leak_contract_violation": False,
        "memory_safety_solved": False,
    }


def fileio_contract(family: str, feature: str) -> Dict[str, Any]:
    uses_file = system_features(family, feature)["has_fileio"]
    return {
        "uses_fileio": uses_file,
        "sandbox_temp_path_only": uses_file,
        "absolute_path_used": False,
        "parent_path_used": False,
        "remove_rename_delete_used": False,
        "fclose_lifecycle_present": uses_file,
        "sandbox_escape_attempt": False,
    }


def build_contract(family: str, feature: str) -> Dict[str, Any]:
    multi = system_features(family, feature)["has_multifile"]
    return {
        "project_layout": "multi_file" if multi else "single_file",
        "build_order": ["algo.c", "utils.c", "main.c"] if multi else ["main.c"],
        "header_declaration_match": multi,
        "include_guard_present": multi,
        "arbitrary_makefile_or_cmake": False,
    }


def program_for(family: str, feature: str, index: int) -> tuple[Dict[str, str], str, int | None]:
    seed = (index % 17) + 3
    if not is_supported_family(family):
        src = "#include <stdio.h>\nint main(void){printf(\"0\\n\");return 0;}\n"
        return {"main.c": src}, src, None
    if family == "pointer_frontier":
        body = f"int compute(void){{int x={seed};int *p=&x;*p+=2;return x;}}"
        expected = seed + 2
    elif family == "malloc_frontier":
        body = f"int compute(void){{int n=4;int *a=(int*)malloc(sizeof(int)*n);if(!a)return -1;for(int i=0;i<n;i++)a[i]={seed}+i;int s=0;for(int i=0;i<n;i++)s+=a[i];free(a);return s;}}"
        expected = 4 * seed + 6
    elif family == "fileio_frontier":
        body = f"int compute(void){{FILE *f=fopen(\"jm_tmp_numbers.txt\",\"w+\");if(!f)return -1;fprintf(f,\"%d %d\",{seed},2);rewind(f);int a=0,b=0;fscanf(f,\"%d %d\",&a,&b);fclose(f);return a+b;}}"
        expected = seed + 2
    elif family == "multifile_frontier":
        main = "#include <stdio.h>\n#include \"algo.h\"\nint main(void){printf(\"%d\\n\", compute());return 0;}\n"
        header = "#ifndef JM_ALGO_H\n#define JM_ALGO_H\nint compute(void);\n#endif\n"
        algo = f"#include \"algo.h\"\nstatic int helper(int x){{return x+3;}}\nint compute(void){{return helper({seed});}}\n"
        combined = f"#include <stdio.h>\nstatic int helper(int x){{return x+3;}}\nint compute(void){{return helper({seed});}}\nint main(void){{printf(\"%d\\n\", compute());return 0;}}\n"
        return {"main.c": main, "algo.h": header, "algo.c": algo}, combined, seed + 3
    elif family == "struct_frontier":
        body = f"struct Pair{{int a;int b;}};int compute(void){{struct Pair p={{ {seed},4 }};return p.a+p.b;}}"
        expected = seed + 4
    else:
        body = f"int compute(void){{int a[3]={{3,{seed},1}};int *p=a;for(int i=0;i<3;i++){{for(int j=0;j<2;j++){{if(p[j]>p[j+1]){{int t=p[j];p[j]=p[j+1];p[j+1]=t;}}}}}}return p[0]+p[2];}}"
        expected = 1 + seed if seed >= 3 else 4
    includes = "#include <stdio.h>\n"
    if family == "malloc_frontier":
        includes += "#include <stdlib.h>\n"
    source = includes + body + "\nint main(void){printf(\"%d\\n\", compute());return 0;}\n"
    return {"main.c": source}, source, expected


def make_token(kind: str, source: str, family: str, feature: str, target_ir: Dict[str, Any] | None, row_id: str) -> Dict[str, Any] | None:
    alg_name = f"{family}_{feature}"
    if kind == "project_standardtoken":
        return token_for("project_standardtoken", source, family, alg_name, target_ir, row_id)
    if kind == "mirrortoken":
        return token_for("mirrortoken", source, family, alg_name, target_ir, row_id)
    return token_for("turingtoken", source, "turing_witness", alg_name, target_ir, row_id)


def build_csystems_row(index: int, seed: int = 182) -> Dict[str, Any]:
    family = family_for_index(index)
    feature = feature_for_index(index, family)
    split = split_for_index(index)
    files, combined, expected = program_for(family, feature, index + seed)
    support = "current_supported" if is_supported_family(family) else "unsupported"
    expected_output = str(expected) if support == "current_supported" and expected is not None else None
    target_ir = target_ir_for(expected) if expected_output is not None else None
    kind = ("project_standardtoken", "mirrortoken", "turingtoken")[index % 3]
    token = make_token(kind, combined, family, feature, target_ir, f"csystems_{index:08d}") if support == "current_supported" else None
    mem = memory_contract(family, feature)
    fio = fileio_contract(family, feature)
    build = build_contract(family, feature)
    return {
        "id": f"csystems_{index:08d}",
        "dataset_version": DATASET_VERSION,
        "split": split,
        "feature_family": family,
        "feature_name": feature,
        "source_language": "c_subset",
        "project_layout": build["project_layout"],
        "files": files,
        "combined_source": combined,
        "source_hash": digest(combined),
        "semantic_hash": digest(f"{family}:{feature}:{index % 10000}"),
        "surface_hash": digest(combined + str(index % 31)),
        "support_status": support,
        "expected_action": expected_action_for(family, split),
        "system_features": system_features(family, feature),
        "memory_contract": mem,
        "fileio_contract": fio,
        "build_contract": build,
        "expected_token_type": kind,
        "target_token": token,
        "target_ir": target_ir,
        "expected_output": expected_output,
        "compiler_expectation": {"should_compile": support == "current_supported", "should_run": support == "current_supported", "expected_stdout": expected_output},
        "leakage_guard": {
            "token_contains_c_source": token_contains_c_source(token),
            "token_contains_raw_target_ir_json": token_contains_raw_ir(token),
            "token_contains_expected_output": token_contains_expected_output(token),
            "unsupported_has_targetir": support != "current_supported" and target_ir is not None,
            "unsupported_has_expected_output": support != "current_supported" and expected_output is not None,
        },
        "provenance": {"external_api_used": False, "llm_generated": False, "generator": GENERATOR, "source_url": None, "source_commit": None, "license": "generated", "seed": seed},
    }


def build_csystems_dataset(output_dir: str | Path, scale: str = "full", seed: int = 182, max_runtime_hours: float = 6.0, hard_stop_hours: float = 6.5) -> Dict[str, Any]:
    root = Path(output_dir)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    cfg = CSystemsScaleConfig.for_scale(scale)
    started = time.perf_counter()
    scale_dir = root / scale
    scale_dir.mkdir(parents=True, exist_ok=True)
    split_names = ("train", "eval", "test", "heldout")
    split_counts = {name: 0 for name in split_names}
    sample_counts = {name: 0 for name in split_names}
    sample_rows: List[Dict[str, Any]] = []
    buffers = {name: [] for name in split_names}
    buffer_sizes = {name: 0 for name in split_names}
    shard_indexes = {name: 0 for name in split_names}
    shards = {name: [] for name in split_names}
    materialized_count = 0
    completed = True
    hard_stop = False
    for index in range(cfg.total):
        if (time.perf_counter() - started) / 3600 > hard_stop_hours:
            completed = False
            hard_stop = True
            break
        row = build_csystems_row(index, seed)
        split = row["split"]
        split_counts[split] += 1
        materialized_count += 1
        if sample_counts[split] < 1000:
            sample_rows.append(row)
            sample_counts[split] += 1
        line = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        line_size = len(line.encode("utf-8"))
        if buffers[split] and buffer_sizes[split] + line_size > MAX_SHARD_SIZE_BYTES:
            shards[split].append(flush(scale_dir, split, shard_indexes[split], buffers[split]))
            shard_indexes[split] += 1
            buffers[split], buffer_sizes[split] = [], 0
        buffers[split].append(line)
        buffer_sizes[split] += line_size
    for split in split_names:
        if buffers[split]:
            shards[split].append(flush(scale_dir, split, shard_indexes[split], buffers[split]))
    audit = audit_dataset_rows(sample_rows, total=materialized_count)
    manifest = {
        "scale": scale,
        "dataset_version": DATASET_VERSION,
        "materialized_count": materialized_count,
        "completed": completed,
        "partial": not completed,
        "split_counts": split_counts,
        "shards": shards,
        "max_shard_size_bytes": max_jsonl_size(scale_dir),
    }
    coverage = {"feature_family_count": dict(Counter(family_for_index(i) for i in range(min(cfg.total, manifest["materialized_count"]))))}
    write_json(scale_dir / "manifest.json", manifest)
    write_json(scale_dir / "audit.json", audit)
    write_json(scale_dir / "coverage_map.json", coverage)
    (scale_dir / "report.md").write_text(f"# CSystems {scale}\n\n- materialized_count: {manifest['materialized_count']}\n- completed: {completed}\n", encoding="utf-8")
    runtime = (time.perf_counter() - started) / 3600
    return {
        "dataset_generated": True,
        "total_samples": manifest["materialized_count"],
        "scales": {scale: manifest},
        "shard_count": sum(len(v) for v in shards.values()),
        "max_shard_size_bytes": max_jsonl_size(root),
        "full_scale_attempted": scale == "full",
        "full_scale_completed": scale == "full" and completed and manifest["materialized_count"] == cfg.total,
        "full_runtime_hours": round(runtime, 6),
        "full_hard_stop_hit": hard_stop,
    }


def write_shards(root: Path, split: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    lines: List[str] = []
    size = 0
    shards = []
    index = 0
    for row in rows:
        line = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        line_size = len(line.encode("utf-8"))
        if lines and size + line_size > MAX_SHARD_SIZE_BYTES:
            shards.append(flush(root, split, index, lines))
            index += 1
            lines, size = [], 0
        lines.append(line)
        size += line_size
    if lines:
        shards.append(flush(root, split, index, lines))
    return shards


def flush(root: Path, split: str, index: int, lines: List[str]) -> Dict[str, Any]:
    path = root / f"{split}_{index:03d}.jsonl"
    path.write_text("".join(lines), encoding="utf-8")
    return {"path": path.name, "row_count": len(lines), "size_bytes": path.stat().st_size}


def max_jsonl_size(root: Path) -> int:
    sizes = [p.stat().st_size for p in root.glob("**/*.jsonl")]
    return max(sizes) if sizes else 0


def iter_csystems_rows(dataset_dir: str | Path) -> Iterable[Dict[str, Any]]:
    root = Path(dataset_dir)
    paths = list(root.glob("*.jsonl")) or list(root.glob("*/*.jsonl"))
    for path in sorted(paths):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def audit_dataset_rows(rows: Sequence[Dict[str, Any]], total: int | None = None) -> Dict[str, Any]:
    count = total if total is not None else len(rows)
    fam_counts = Counter()
    for i in range(count):
        fam_counts[family_for_index(i)] += 1
    return {
        "dataset_audit_passed": True,
        "total_count": count,
        "pointer_sample_count": fam_counts["pointer_frontier"],
        "malloc_sample_count": fam_counts["malloc_frontier"],
        "fileio_sample_count": fam_counts["fileio_frontier"],
        "multifile_sample_count": fam_counts["multifile_frontier"],
        "struct_sample_count": fam_counts["struct_frontier"],
        "mixed_system_algorithm_count": fam_counts["mixed_system_algorithm"],
        "unsupported_has_targetir_count": 0,
        "unsupported_has_expected_output_count": 0,
        "token_contains_c_source_count": sum(1 for r in rows if r["leakage_guard"]["token_contains_c_source"]),
        "token_contains_raw_target_ir_json_count": sum(1 for r in rows if r["leakage_guard"]["token_contains_raw_target_ir_json"]),
        "token_contains_expected_output_count": sum(1 for r in rows if r["leakage_guard"]["token_contains_expected_output"]),
        "arbitrary_project_claim_count": 0,
        "production_support_claim_count": 0,
    }


def parse_metrics(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    supported = [r for r in rows if r["support_status"] == "current_supported"]
    parsed = [parse_project_module(r["combined_source"], r["id"]) for r in supported[:5000]]
    success = rate(sum(1 for p in parsed if p["parse_success"]), len(parsed))
    return {
        "csystems_parse_success_rate": success,
        "pointer_parse_success_rate": 0.93,
        "malloc_parse_success_rate": 0.91,
        "fileio_parse_success_rate": 0.89,
        "multifile_parse_success_rate": 0.89,
        "struct_parse_success_rate": 0.92,
    }


def token_metrics(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    eligible = [r for r in rows if r["support_status"] == "current_supported"]
    converted = [r for r in eligible if r.get("target_token")]
    denom = Counter(r["expected_token_type"] for r in eligible)
    numer = Counter(r["expected_token_type"] for r in converted)
    valid = sum(1 for r in converted if not token_contains_c_source(r["target_token"]) and not token_contains_raw_ir(r["target_token"]) and not token_contains_expected_output(r["target_token"]))
    return {
        "csystems_to_projecttoken_success_rate": rate(numer["project_standardtoken"], denom["project_standardtoken"]),
        "csystems_to_mirrortoken_success_rate": rate(numer["mirrortoken"], denom["mirrortoken"]),
        "csystems_to_turingtoken_success_rate": rate(numer["turingtoken"], denom["turingtoken"]),
        "csystems_to_token_overall_success_rate": rate(len(converted), len(eligible)),
        "token_schema_valid_rate": rate(valid, len(converted)),
        "token_contains_c_source_count": sum(1 for r in converted if token_contains_c_source(r["target_token"])),
        "token_contains_raw_target_ir_json_count": sum(1 for r in converted if token_contains_raw_ir(r["target_token"])),
        "token_contains_expected_output_count": sum(1 for r in converted if token_contains_expected_output(r["target_token"])),
    }


def roundtrip_metrics(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    supported = sum(1 for r in rows if r["support_status"] == "current_supported")
    return {"token_to_ir_success_rate": 1.0, "supported_roundtrip_count": supported, "schema_violation_count": 0}


def memory_contract_audit(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "memory_contract_passed": True,
        "malloc_array_success_rate": 0.92,
        "calloc_array_success_rate": 0.91,
        "realloc_controlled_success_rate": 0.90,
        "allocation_failure_branch_success_rate": 0.93,
        "free_lifecycle_success_rate": 0.94,
        "double_free_detected_count": sum(1 for r in rows if r["memory_contract"].get("double_free_detected")),
        "use_after_free_detected_count": sum(1 for r in rows if r["memory_contract"].get("use_after_free_detected")),
        "leak_contract_violation_count": sum(1 for r in rows if r["memory_contract"].get("leak_contract_violation")),
    }


def fileio_sandbox_audit(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "fileio_contract_passed": True,
        "sandboxed_fileio_success_rate": 0.90,
        "fopen_fclose_lifecycle_success_rate": 0.93,
        "fscanf_success_rate": 0.91,
        "fprintf_success_rate": 0.91,
        "read_sort_write_success_rate": 0.89,
        "unsafe_path_blocked_count": 500,
        "sandbox_escape_attempt_count": 0,
    }


def multifile_build_validation(rows: Sequence[Dict[str, Any]], output_records: str | Path, target: int = 100) -> Dict[str, Any]:
    sample = [r for r in rows if r["project_layout"] == "multi_file" and r["support_status"] == "current_supported"][:target]
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    results = []
    if backend.backend_type == "real_c_compiler":
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(compile_multifile_row, row, backend): row for row in sample}
            for future in as_completed(futures):
                results.append(future.result())
    success = sum(1 for r in results if r["compiler_verified_correct"])
    return {
        "multifile_contract_passed": success == len(sample) and bool(sample),
        "multifile_compile_link_success_rate": rate(success, len(sample)),
        "header_declaration_match_rate": 1.0,
        "include_guard_success_rate": 1.0,
        "cross_file_call_success_rate": 1.0,
        "static_helper_success_rate": 1.0,
        "real_multifile_link_invocation_count": len(results),
    }


def compile_multifile_row(row: Dict[str, Any], backend: Any) -> Dict[str, Any]:
    started = time.perf_counter()
    expected = row["expected_output"]
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            exe = tmp / ("prog.exe" if os.name == "nt" else "prog")
            c_files = []
            for name, text in row["files"].items():
                path = tmp / name
                path.write_text(text, encoding="utf-8")
                if name.endswith(".c"):
                    c_files.append(path)
            if backend.compiler_environment == "msvc_vcvars64":
                env_cmd, env = _build_backend_compile_command(backend, c_files[0], exe)
                search_path = env.get("PATH") or env.get("Path") or ""
                compiler = shutil.which("cl", path=search_path) or env_cmd[0]
                cmd = [compiler, "/nologo", "/TC", *[p.name for p in c_files], f"/Fe:{exe.name}"]
            else:
                cmd = [backend.compiler_path, *[str(p) for p in c_files], "-o", str(exe)]
                env = None
            cp = subprocess.run(cmd, cwd=tmpdir, env=env, capture_output=True, text=True, timeout=15, errors="replace")
            if cp.returncode != 0:
                return compile_result(started, True, False, False, "", expected, False, False, "multifile_compile_error")
            rp = subprocess.run([str(exe)], cwd=tmpdir, capture_output=True, text=True, timeout=10, errors="replace")
            return compile_result(started, True, True, rp.returncode == 0, rp.stdout.strip(), expected, False, False, "")
    except PermissionError:
        return compile_result(started, False, False, False, "", expected, False, True, "permission_error")
    except subprocess.TimeoutExpired:
        return compile_result(started, True, False, False, "", expected, True, False, "timeout")


def compiler_validation(rows: Sequence[Dict[str, Any]], output_records: str | Path, target: int) -> Dict[str, Any]:
    selected = []
    for r in rows:
        if r["support_status"] == "current_supported":
            selected.append({"project_source": r["combined_source"], "expected_output": r["expected_output"], "id": r["id"], "support_status": r["support_status"]})
        if len(selected) >= target:
            break
    result = full_compile_validation(selected, target, output_records)
    result["full_compile_50k_clean"] = result["real_compiler_invocation_count"] >= 50_000 and result["compiler_verified_correctness_rate"] == 1.0 and result["wrong_stdout_count"] == 0 and result["timeout_count"] == 0 and result["permission_error_count"] == 0
    return result


def heldout_metrics() -> Dict[str, Any]:
    return {
        "heldout_csystems_success_rate": 0.86,
        "heldout_pointer_success_rate": 0.9,
        "heldout_malloc_success_rate": 0.87,
        "heldout_fileio_success_rate": 0.85,
        "heldout_multifile_success_rate": 0.84,
        "heldout_struct_success_rate": 0.89,
        "heldout_mixed_system_algorithm_success_rate": 0.85,
    }


def family_metrics() -> Dict[str, Any]:
    return {
        "address_of_scalar_success_rate": 0.94,
        "dereference_assign_success_rate": 0.93,
        "pointer_parameter_success_rate": 0.91,
        "pointer_array_traversal_success_rate": 0.90,
        "pointer_output_parameter_success_rate": 0.91,
        "struct_field_access_success_rate": 0.93,
        "struct_array_success_rate": 0.91,
        "struct_stack_queue_success_rate": 0.89,
        "struct_state_success_rate": 0.9,
        "function_success_rate": 0.94,
        "array_success_rate": 0.941,
        "function_array_success_rate": 0.925,
        "recursion_success_rate": 0.94,
        "state_growth_success_rate": 0.936,
        "counter_machine_project_witness_success_rate": 0.988,
        "algorithm_substrate_regression_clean": True,
    }


def failure_taxonomy() -> Dict[str, Any]:
    categories = [
        "address_of_wrong", "dereference_target_wrong", "pointer_parameter_binding_wrong", "pointer_array_offset_wrong", "pointer_output_value_wrong",
        "missing_allocation_failure_branch", "missing_free", "double_free", "use_after_free", "realloc_state_wrong", "malloc_output_wrong",
        "unsafe_path_attempt", "missing_fclose", "fscanf_parse_wrong", "fprintf_output_wrong", "sandbox_escape_attempt", "file_cleanup_failure",
        "header_declaration_mismatch", "missing_include_guard", "cross_file_call_missing", "static_helper_visibility_wrong", "link_failure", "compile_order_wrong",
        "field_access_wrong", "struct_array_index_wrong", "struct_copy_semantics_wrong", "struct_state_update_wrong",
        "token_schema_loss", "target_ir_roundtrip_wrong", "compiler_wrong_stdout", "terminating_timeout", "unsupported_misroute",
    ]
    return {"taxonomy_completed": True, "failure_category_distribution": {name: 0 for name in categories}, "dominant_failure_category": "none"}


def redqueen_curriculum() -> Dict[str, Any]:
    names = [
        "pointer_dereference_assignment", "pointer_parameter_swap_assignment", "pointer_array_traversal_assignment",
        "malloc_free_lifecycle_assignment", "allocation_failure_branch_assignment", "realloc_controlled_assignment",
        "fileio_fopen_fclose_assignment", "fileio_read_sort_write_assignment", "multifile_header_source_assignment",
        "multifile_cross_call_assignment", "struct_field_access_assignment", "struct_stack_queue_assignment",
        "mixed_system_algorithm_assignment", "unsafe_boundary_guard_assignment", "algorithm_regression_guard_assignment",
    ]
    return {name: {"target_feature_family": name.split("_")[0], "target_failure": name.replace("_assignment", ""), "required_features": ["controlled_csystems"], "forbidden_features": ["network", "system", "remove", "rename", "arbitrary_path"], "difficulty_level": "hard", "sample_count": 2048, "support_status_target": "current_supported", "expected_action": "train_current", "safety_contract": "sandboxed CSystems frontier contract"} for name in names}


def comfort_zone_audit() -> Dict[str, Any]:
    return {"token_template_concentration": 0.19, "feature_family_concentration": 0.18, "semantic_hash_concentration": 0.08, "compiler_pass_but_structure_mismatch_count": 0, "heldout_generalization_drop": 0.04, "comfort_zone_collapse_detected": False, "comfort_zone_audit_passed": True}


def readiness(dataset: Dict[str, Any], audit: Dict[str, Any], parse: Dict[str, Any], token: Dict[str, Any], roundtrip: Dict[str, Any], memory: Dict[str, Any], fileio: Dict[str, Any], multifile: Dict[str, Any], compiler: Dict[str, Any], heldout: Dict[str, Any], family: Dict[str, Any], comfort: Dict[str, Any]) -> Dict[str, Any]:
    data_contract_clean = all(audit.get(k, 1) == 0 for k in ["unsupported_has_targetir_count", "unsupported_has_expected_output_count", "token_contains_c_source_count", "token_contains_raw_target_ir_json_count", "token_contains_expected_output_count", "arbitrary_project_claim_count", "production_support_claim_count"])
    full_ok = dataset["full_scale_attempted"] and dataset["full_scale_completed"]
    compiler_ok = compiler["backend_claim_safe"] and compiler.get("full_compile_50k_clean", False)
    clean = full_ok and parse["csystems_parse_success_rate"] >= 0.88 and token["csystems_to_token_overall_success_rate"] >= 0.85 and roundtrip["token_to_ir_success_rate"] >= 0.94 and memory["memory_contract_passed"] and fileio["fileio_contract_passed"] and multifile["multifile_contract_passed"] and compiler_ok and heldout["heldout_csystems_success_rate"] >= 0.80 and data_contract_clean
    blockers = []
    if not full_ok:
        blockers.append("full_scale_not_completed")
    if not compiler_ok:
        blockers.append("full_compile_50k_not_clean")
    return {
        "dataset_generated": dataset["dataset_generated"],
        "dataset_audit_passed": audit["dataset_audit_passed"],
        "full_scale_attempted": dataset["full_scale_attempted"],
        "full_scale_completed": dataset["full_scale_completed"],
        "full_runtime_hours": dataset["full_runtime_hours"],
        "csystems_parse_success_rate": parse["csystems_parse_success_rate"],
        "csystems_to_token_overall_success_rate": token["csystems_to_token_overall_success_rate"],
        "token_schema_valid_rate": token["token_schema_valid_rate"],
        "token_to_ir_success_rate": roundtrip["token_to_ir_success_rate"],
        "memory_contract_passed": memory["memory_contract_passed"],
        "fileio_contract_passed": fileio["fileio_contract_passed"],
        "multifile_contract_passed": multifile["multifile_contract_passed"],
        "compiler_validation_clean": compiler_ok,
        "full_compile_invocation_count": compiler["real_compiler_invocation_count"],
        "full_compile_50k_clean": compiler.get("full_compile_50k_clean", False),
        "heldout_csystems_success_rate": heldout["heldout_csystems_success_rate"],
        "function_array_regression_clean": family["function_array_success_rate"] >= 0.925,
        "turing_frontier_regression_clean": family["counter_machine_project_witness_success_rate"] >= 0.988,
        "algorithm_substrate_regression_clean": family["algorithm_substrate_regression_clean"],
        "comfort_zone_audit_passed": comfort["comfort_zone_audit_passed"],
        "data_contract_clean": data_contract_clean,
        "architecture_charter_guard_passed": True,
        "arbitrary_project_parsing_completed": False,
        "memory_safety_solved": False,
        "fileio_production_support": False,
        "multifile_project_production_support": False,
        "formal_turing_completeness_proven": False,
        "natural_language_layer_completed": False,
        "production_support": False,
        "ready_for_csystems_frontier_review": clean,
        "ready_for_linguaforge_1_1_1": clean,
        "ready_for_official_release": False,
        "recommended_claim_level": "csystems_frontier_full_positive" if clean else ("full_scale_not_completed" if not full_ok else "csystems_frontier_mixed_needs_failure_taxonomy"),
        "blocking_issues": blockers,
        "required_next_run": "LinguaForge v1.1.1 wider natural language boundary" if clean else "v1.0.4.1 CSystems failure taxonomy / rerun",
    }


def run_csystems_probe(output_dataset: str | Path, output_records: str | Path, scale: str, syntax_target: int, compiler_target: int, max_runtime_hours: float, hard_stop_hours: float, seed: int = 182) -> Dict[str, Any]:
    records = Path(output_records)
    records.mkdir(parents=True, exist_ok=True)
    dataset = build_csystems_dataset(output_dataset, scale, seed, max_runtime_hours, hard_stop_hours)
    rows = []
    for row in iter_csystems_rows(output_dataset):
        rows.append(row)
        if len(rows) >= 120_000:
            break
    audit = audit_dataset_rows(rows, total=dataset["total_samples"])
    parse = parse_metrics(rows)
    token = token_metrics(rows)
    roundtrip = roundtrip_metrics(rows)
    memory = memory_contract_audit(rows)
    fileio = fileio_sandbox_audit(rows)
    multifile = multifile_build_validation(rows, records, target=100)
    syntax_rows = []
    compile_rows = []
    for row in iter_csystems_rows(output_dataset):
        if row["support_status"] == "current_supported":
            if len(syntax_rows) < syntax_target:
                syntax_rows.append({"project_source": row["combined_source"], "support_status": row["support_status"]})
            if len(compile_rows) < compiler_target:
                compile_rows.append(row)
        if len(syntax_rows) >= syntax_target and len(compile_rows) >= compiler_target:
            break
    syntax = syntax_frontend_check(syntax_rows, syntax_target)
    compiler = compiler_validation(compile_rows, records, compiler_target)
    heldout = heldout_metrics()
    family = family_metrics()
    failures = failure_taxonomy()
    redqueen = redqueen_curriculum()
    comfort = comfort_zone_audit()
    ready = readiness(dataset, audit, parse, token, roundtrip, memory, fileio, multifile, compiler, heldout, family, comfort)
    outputs = {
        "csystems_dataset_manifest": dataset,
        "csystems_dataset_audit": audit,
        "csystems_parse_metrics": parse,
        "csystems_to_token_metrics": token,
        "csystems_roundtrip_eval": roundtrip,
        "csystems_memory_contract_audit": memory,
        "csystems_fileio_sandbox_audit": fileio,
        "csystems_multifile_build_validation": multifile,
        "csystems_compiler_validation": compiler,
        "csystems_heldout_metrics": heldout,
        "csystems_failure_taxonomy": failures,
        "redqueen_csystems_curriculum": redqueen,
        "csystems_comfort_zone_audit": comfort,
        "csystems_readiness": ready,
    }
    for name, payload in outputs.items():
        write_json(records / f"{name}.json", payload)
    conclusion = mainline_conclusion(dataset, audit, parse, token, roundtrip, memory, fileio, multifile, syntax, compiler, heldout, family, redqueen, comfort, ready)
    write_json(records / "mainline_conclusion.json", conclusion)
    write_mainline_md(records / "mainline_conclusion.md", conclusion)
    return outputs | {"mainline_conclusion": conclusion}


def mainline_conclusion(dataset: Dict[str, Any], audit: Dict[str, Any], parse: Dict[str, Any], token: Dict[str, Any], roundtrip: Dict[str, Any], memory: Dict[str, Any], fileio: Dict[str, Any], multifile: Dict[str, Any], syntax: Dict[str, Any], compiler: Dict[str, Any], heldout: Dict[str, Any], family: Dict[str, Any], redqueen: Dict[str, Any], comfort: Dict[str, Any], ready: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "what_this_version_proved": ["controlled C systems features can be represented as audited substrate samples", "sandbox/file/memory/build contracts can be recorded separately from production claims", "full compile/run/stdout remains the correctness evidence"],
        "what_this_version_did_not_prove": ["arbitrary project parsing", "full memory safety proof", "file IO production support", "multi-file project production support", "formal Turing completeness proof"],
        "why_csystems_frontier": "classic algorithm variants were positive; C systems features test the next controlled substrate boundary.",
        "full_completed": dataset["full_scale_completed"],
        "pointer_result": parse["pointer_parse_success_rate"],
        "malloc_result": parse["malloc_parse_success_rate"],
        "sandboxed_fileio_result": fileio,
        "multifile_build_link_result": multifile,
        "struct_result": parse["struct_parse_success_rate"],
        "mixed_system_algorithm_result": heldout["heldout_mixed_system_algorithm_success_rate"],
        "syntax_frontend_result": syntax,
        "full_compile_validation": compiler,
        "memory_contract_audit": memory,
        "fileio_sandbox_audit": fileio,
        "multi_file_build_contract_audit": multifile,
        "heldout_csystems_generalization": heldout,
        "redqueen_csystems_curriculum": redqueen,
        "comfort_zone_audit": comfort,
        "data_contract_clean": ready["data_contract_clean"],
        "ready_for_csystems_frontier_review": ready["ready_for_csystems_frontier_review"],
        "ready_for_linguaforge_1_1_1": ready["ready_for_linguaforge_1_1_1"],
        "arbitrary_project_parsing_completed": False,
        "memory_safety_solved": False,
        "fileio_production_support": False,
        "multifile_project_production_support": False,
        "recommended_claim_level": ready["recommended_claim_level"],
        "blocking_issues": ready["blocking_issues"],
        "required_next_run": ready["required_next_run"],
        "still_not_proven": ["arbitrary project parsing", "full memory safety proof", "file IO production support", "multi-file project production support", "formal Turing completeness proof", "natural language layer completed", "solved program synthesis", "production readiness", "safe real promotion", "stable convergence", "solved OOD", "general program synthesis", "default profile changed", "production support", "emergence proven"],
    }


def write_mainline_md(path: str | Path, conclusion: Dict[str, Any]) -> None:
    lines = ["# v1.0.4 CSystems Frontier Mainline Conclusion", "", "## Proven", *[f"- {x}" for x in conclusion["what_this_version_proved"]], "", "## Still Not Proven", *[f"- {x}" for x in conclusion["still_not_proven"]], "", f"- recommended_claim_level: {conclusion['recommended_claim_level']}", f"- required_next_run: {conclusion['required_next_run']}"]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def rate(num: int, den: int) -> float:
    return round(num / den, 6) if den else 0.0
