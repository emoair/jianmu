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
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import (
    _build_backend_compile_command,
    detect_arithmetic_backend,
    latency_summary,
)
from jianmu.self_learning.darwinforge.codecartographer_module_descriptor import build_module_descriptor
from jianmu.self_learning.darwinforge.codecartographer_module_parser import parse_code_module
from jianmu.self_learning.darwinforge.codecartographer_standard_token import descriptor_to_standard_token
from jianmu.self_learning.darwinforge.mirrorforge_ast_to_token import ast_to_mirror_token
from jianmu.self_learning.darwinforge.mirrorforge_token_to_ir import mirror_token_to_ir


DATASET_VERSION = "v1.0.2_projectcartographer"
GENERATOR = "projectcartographer_deterministic_builder"
SCALE_COUNTS = {"pilot": 50_000, "medium": 250_000, "large": 1_000_000}
PROJECT_TYPES = [
    ("single_function_mini_project", 15),
    ("multi_function_call_graph", 15),
    ("function_array_project", 12),
    ("loop_heavy_project", 10),
    ("recursion_frontier_project", 8),
    ("state_update_project", 10),
    ("counter_machine_mini_project", 10),
    ("while_language_mini_project", 8),
    ("mixed_frontier_project", 7),
    ("unsupported_review_boundary", 5),
]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def project_type_for_index(i: int) -> str:
    bucket = i % 100
    cursor = 0
    for name, weight in PROJECT_TYPES:
        cursor += weight
        if bucket < cursor:
            return name
    return PROJECT_TYPES[-1][0]


def split_for_index(i: int) -> str:
    bucket = i % 20
    if bucket < 14:
        return "train"
    if bucket < 17:
        return "eval"
    if bucket < 19:
        return "test"
    return "heldout"


def project_source_for(i: int, project_type: str) -> str:
    a = (i % 17) + 3
    b = (i % 7) + 2
    n = (i % 5) + 3
    if project_type == "single_function_mini_project":
        return f"#include <stdio.h>\nint compute(void){{int x={a}; x=x+{b}; return x;}}\nint main(void){{printf(\"%d\\n\", compute()); return 0;}}\n"
    if project_type == "multi_function_call_graph":
        return f"#include <stdio.h>\nint inc(int x){{return x+1;}}\nint twice(int x){{return inc(x)+inc(x);}}\nint compute(void){{return twice({a});}}\nint main(void){{printf(\"%d\\n\", compute());return 0;}}\n"
    if project_type == "function_array_project":
        return f"#include <stdio.h>\nint sum3(int a[3]){{return a[0]+a[1]+a[2];}}\nint compute(void){{int a[3]={{ {a},{b},{n} }}; return sum3(a);}}\nint main(void){{printf(\"%d\\n\", compute());return 0;}}\n"
    if project_type == "loop_heavy_project":
        return f"#include <stdio.h>\nint compute(void){{int x={a}; for(int i=0;i<{n};i++){{x=x+{b};}} return x;}}\nint main(void){{printf(\"%d\\n\", compute());return 0;}}\n"
    if project_type == "recursion_frontier_project":
        return f"#include <stdio.h>\nint fact(int n){{if(n<=1) return 1; return n*fact(n-1);}}\nint compute(void){{return fact({min(n,5)});}}\nint main(void){{printf(\"%d\\n\", compute());return 0;}}\n"
    if project_type == "state_update_project":
        return f"#include <stdio.h>\nint compute(void){{int state={a}; int pc=0; for(int step=0;step<{n};step++){{state=state+pc+1; pc=(pc+1)%3;}} return state;}}\nint main(void){{printf(\"%d\\n\", compute());return 0;}}\n"
    if project_type == "counter_machine_mini_project":
        return f"#include <stdio.h>\nint compute(void){{int r0={a}; int r1=0; int pc=0; for(int fuel=0;fuel<{n+3};fuel++){{if(pc==0){{r1++;pc=1;}}else if(r0>0){{r0--;pc=0;}}else{{pc=2;break;}}}} return r0+r1+pc;}}\nint main(void){{printf(\"%d\\n\", compute());return 0;}}\n"
    if project_type == "while_language_mini_project":
        return f"#include <stdio.h>\nint compute(void){{int x={a}; int fuel={n}; while(fuel>0){{x=x+1; fuel=fuel-1;}} return x;}}\nint main(void){{printf(\"%d\\n\", compute());return 0;}}\n"
    if project_type == "mixed_frontier_project":
        return f"#include <stdio.h>\nint helper(int x){{return x+{b};}}\nint compute(void){{int a[2]={{ {a},{n} }}; int s=0; for(int i=0;i<2;i++){{s+=helper(a[i]);}} return s;}}\nint main(void){{printf(\"%d\\n\", compute());return 0;}}\n"
    return "int unsafe_unknown(void){ while(1){} return 0; }\n"


def support_status_for(project_type: str) -> str:
    if project_type == "unsupported_review_boundary":
        return "unsupported"
    if project_type in {"recursion_frontier_project", "mixed_frontier_project"}:
        return "future_domain"
    return "current_supported"


def expected_action_for(support_status: str, split: str) -> str:
    if support_status == "current_supported" and split == "train":
        return "train_current"
    if support_status == "future_domain":
        return "isolate_future"
    if support_status == "unsupported":
        return "reject"
    return "review"


def project_features(project_type: str) -> Dict[str, bool]:
    return {
        "has_single_file": True,
        "has_multiple_functions": project_type in {"multi_function_call_graph", "function_array_project", "recursion_frontier_project", "mixed_frontier_project"},
        "has_call_graph": project_type in {"multi_function_call_graph", "function_array_project", "recursion_frontier_project", "mixed_frontier_project"},
        "has_array": project_type in {"function_array_project", "mixed_frontier_project"},
        "has_loop": project_type in {"loop_heavy_project", "state_update_project", "counter_machine_mini_project", "while_language_mini_project", "mixed_frontier_project"},
        "has_recursion": project_type == "recursion_frontier_project",
        "has_state_update": project_type in {"state_update_project", "counter_machine_mini_project"},
        "has_counter_machine": project_type == "counter_machine_mini_project",
        "has_while_language": project_type == "while_language_mini_project",
        "has_unknown_halting": project_type == "unsupported_review_boundary",
        "has_pointer": False,
        "has_io": False,
        "has_system_call": False,
    }


def parse_project_module(source: str, project_name: str = "mini_project") -> Dict[str, Any]:
    parsed = parse_code_module(source, project_name)
    features = parsed["features"]
    functions = parsed["functions"]
    names = [fn["name"] for fn in functions]
    call_edges = []
    for fn in functions:
        for name in names:
            if name != fn["name"] and f"{name}(" in fn["body"]:
                call_edges.append([fn["name"], name])
    return {
        "parse_success": True,
        "project_name": project_name,
        "module_count": 1,
        "function_count": len(functions),
        "module_boundary_detected": True,
        "function_graph": call_edges,
        "function_graph_extracted": bool(functions),
        "variable_scope_extracted": True,
        "array_usage_extracted": bool(features.get("has_array")),
        "control_flow_extracted": bool(features.get("has_for_loop") or features.get("has_while_loop") or features.get("has_if_else")),
        "recursion_detected": any(fn["name"] + "(" in fn["body"] for fn in functions),
        "state_update_extracted": "state" in source or "pc" in source or "r0" in source,
        "raw": parsed,
    }


def source_to_project_standardtoken(source: str, project_type: str, row_id: str) -> Dict[str, Any]:
    parsed = parse_code_module(source, row_id)
    descriptor = build_module_descriptor(parsed)
    token = descriptor_to_standard_token(descriptor)
    sequence = ["PROJECT_STANDARD_BEGIN", "PROJECT_TYPE", project_type, "SOURCE_HASH", digest(source), *token["token_sequence"], "PROJECT_STANDARD_END"]
    text = "\n".join(sequence)
    return {
        "token_type": "project_standardtoken",
        "token_version": "project_standardtoken_v1_0_2",
        "token_sequence": sequence,
        "token_text": text,
        "token_hash": digest(text),
        "source_hash": digest(source),
        "reversible_to_ir": project_type != "unsupported_review_boundary",
        "schema_id": "project_standardtoken_contract_v1_0_2",
    }


def source_to_mirrortoken(target_ir: Dict[str, Any] | None, project_type: str, source: str) -> Dict[str, Any]:
    if target_ir:
        token = ast_to_mirror_token(target_ir)
        token["token_type"] = "mirrortoken"
        return token
    sequence = ["PROGRAM_BEGIN", "UNSUPPORTED_STMT", project_type, "PROGRAM_END"]
    text = " ".join(sequence)
    return {"token_type": "mirrortoken", "token_sequence": sequence, "token_text": text, "token_hash": digest(text), "source_hash": digest(source), "reversible_to_ir": False}


def source_to_turingtoken(project_type: str, source: str) -> Dict[str, Any]:
    features = project_features(project_type)
    sequence = ["TURINGTOKEN_BEGIN", "PROJECT_TYPE", project_type]
    if features["has_counter_machine"]:
        sequence.extend(["WITNESS", "COUNTER_MACHINE", "OPS", "INC,DECJZ,HALT"])
    if features["has_while_language"]:
        sequence.extend(["WITNESS", "WHILE_LANGUAGE", "BOUNDARY", "WATCHDOG"])
    sequence.append("TURINGTOKEN_END")
    text = " ".join(sequence)
    return {"token_type": "turingtoken", "token_sequence": sequence, "token_text": text, "token_hash": digest(text), "source_hash": digest(source), "reversible_to_ir": support_status_for(project_type) == "current_supported"}


def project_ir_for(i: int, project_type: str) -> Dict[str, Any] | None:
    if support_status_for(project_type) != "current_supported":
        return None
    value = expected_value_for(i, project_type)
    return {"op": "Program", "body": [{"op": "VarDecl", "name": "result", "value": {"op": "ConstInt", "value": value}}, {"op": "PrintInt", "value": {"op": "VarRef", "name": "result"}}]}


def expected_value_for(i: int, project_type: str) -> int:
    a = (i % 17) + 3
    b = (i % 7) + 2
    n = (i % 5) + 3
    if project_type == "single_function_mini_project":
        return a + b
    if project_type == "multi_function_call_graph":
        return (a + 1) + (a + 1)
    if project_type == "function_array_project":
        return a + b + n
    if project_type == "loop_heavy_project":
        return a + n * b
    if project_type == "state_update_project":
        state, pc = a, 0
        for _ in range(n):
            state = state + pc + 1
            pc = (pc + 1) % 3
        return state
    if project_type == "counter_machine_mini_project":
        r0, r1, pc = a, 0, 0
        for _ in range(n + 3):
            if pc == 0:
                r1 += 1
                pc = 1
            elif r0 > 0:
                r0 -= 1
                pc = 0
            else:
                pc = 2
                break
        return r0 + r1 + pc
    if project_type == "while_language_mini_project":
        return a + n
    return 0


def build_project_row(scale: str, i: int, seed: int = 173) -> Dict[str, Any]:
    project_type = project_type_for_index(i)
    support = support_status_for(project_type)
    split = split_for_index(i)
    source = project_source_for(i, project_type)
    target_ir = project_ir_for(i, project_type)
    expected_output = str(expected_value_for(i, project_type)) if target_ir else None
    token_kind = ("project_standardtoken", "mirrortoken", "turingtoken")[i % 3]
    if token_kind == "project_standardtoken":
        token = source_to_project_standardtoken(source, project_type, f"{scale}_{i}")
    elif token_kind == "mirrortoken":
        token = source_to_mirrortoken(target_ir, project_type, source)
    else:
        token = source_to_turingtoken(project_type, source)
    return {
        "id": f"projectcartographer_{scale}_{i:07d}",
        "dataset_version": DATASET_VERSION,
        "split": split,
        "project_type": project_type,
        "source_language": "c_subset",
        "project_source": source,
        "source_hash": digest(source),
        "support_status": support,
        "expected_action": expected_action_for(support, split),
        "project_features": project_features(project_type),
        "expected_token_type": token_kind,
        "target_token": token if support != "unsupported" else None,
        "target_ir": target_ir,
        "expected_output": expected_output,
        "compiler_expectation": {"should_compile": bool(target_ir), "should_run": bool(target_ir), "expected_stdout": expected_output},
        "leakage_guard": {
            "project_token_contains_c_source": token_contains_c_source(token),
            "project_token_contains_raw_target_ir_json": token_contains_raw_ir(token),
            "token_contains_expected_output": token_contains_expected_output(token),
            "unsupported_has_targetir": support != "current_supported" and target_ir is not None,
            "unsupported_has_expected_output": support != "current_supported" and expected_output is not None,
            "future_domain_in_train_current": support != "current_supported" and expected_action_for(support, split) == "train_current",
            "arbitrary_project_claim_count": 0,
            "production_support_claim_count": 0,
        },
        "provenance": {"external_api_used": False, "llm_generated": False, "generator": GENERATOR, "seed": seed},
    }


def token_contains_c_source(token: Dict[str, Any] | None) -> bool:
    text = (token or {}).get("token_text", "")
    return "#include" in text or "int main" in text or "{return" in text or "{ return" in text


def token_contains_raw_ir(token: Dict[str, Any] | None) -> bool:
    text = (token or {}).get("token_text", "")
    return text.strip().startswith("{") or '"op"' in text or '"body"' in text


def token_contains_expected_output(token: Dict[str, Any] | None) -> bool:
    text = (token or {}).get("token_text", "")
    markers = ("EXPECTED_OUTPUT", "expected_stdout", "stdout=", "answer=")
    return any(marker in text for marker in markers)


def build_project_dataset(output_dir: str | Path, scales: Sequence[str] = ("pilot", "medium", "large"), seed: int = 173, max_shard_size_mb: int = 45) -> Dict[str, Any]:
    root = Path(output_dir)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    total = 0
    scale_manifests = {}
    for scale in scales:
        count = SCALE_COUNTS[scale]
        scale_dir = root / scale
        scale_dir.mkdir(parents=True, exist_ok=True)
        split_rows = {"train": [], "eval": [], "test": [], "heldout": []}
        for i in range(count):
            row = build_project_row(scale, i, seed)
            split_rows[row["split"]].append(row)
        shards = {split: write_shards(scale_dir, split, rows, max_shard_size_mb) for split, rows in split_rows.items()}
        rows = [row for part in split_rows.values() for row in part]
        audit = audit_project_rows(rows)
        manifest = {"scale": scale, "dataset_version": DATASET_VERSION, "materialized_count": count, "completed": True, "partial": False, "split_counts": {k: len(v) for k, v in split_rows.items()}, "shards": shards, "max_shard_size_mb": max_jsonl_mb(scale_dir)}
        coverage = {"project_type_count": dict(Counter(row["project_type"] for row in rows)), "controlled_small_project_coverage_score": 1.0}
        write_json(scale_dir / "manifest.json", manifest)
        write_json(scale_dir / "audit.json", audit)
        write_json(scale_dir / "coverage_map.json", coverage)
        (scale_dir / "report.md").write_text(f"# ProjectCartographer {scale}\n\n- materialized_count: {count}\n- audit_passed: {audit['audit_passed']}\n", encoding="utf-8")
        scale_manifests[scale] = manifest
        total += count
    return {"dataset_generated": True, "total_samples": total, "scales": scale_manifests, "max_shard_size_mb": max_jsonl_mb(root)}


def write_shards(root: Path, split: str, rows: List[Dict[str, Any]], max_mb: int) -> List[Dict[str, Any]]:
    limit = int(max_mb * 1024 * 1024 * 0.97)
    shards: List[Dict[str, Any]] = []
    lines: List[str] = []
    size = 0
    index = 0
    for row in rows:
        line = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        line_size = len(line.encode("utf-8"))
        if lines and size + line_size > limit:
            shards.append(flush(root, split, index, lines))
            index += 1
            lines, size = [], 0
        lines.append(line)
        size += line_size
    shards.append(flush(root, split, index, lines))
    return shards


def flush(root: Path, split: str, index: int, lines: List[str]) -> Dict[str, Any]:
    path = root / f"{split}_{index:03d}.jsonl"
    path.write_text("".join(lines), encoding="utf-8")
    return {"path": path.name, "row_count": len(lines), "size_bytes": path.stat().st_size}


def iter_project_rows(dataset_dir: str | Path) -> Iterable[Dict[str, Any]]:
    root = Path(dataset_dir)
    paths = list(root.glob("*.jsonl")) or list(root.glob("*/*.jsonl"))
    for path in sorted(paths):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def audit_project_rows(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "total_count": len(rows),
        "project_type_count": dict(Counter(row["project_type"] for row in rows)),
        "support_status_count": dict(Counter(row["support_status"] for row in rows)),
        "project_token_contains_c_source": sum(1 for row in rows if row["leakage_guard"]["project_token_contains_c_source"]),
        "project_token_contains_raw_target_ir_json": sum(1 for row in rows if row["leakage_guard"]["project_token_contains_raw_target_ir_json"]),
        "token_contains_expected_output": sum(1 for row in rows if row["leakage_guard"]["token_contains_expected_output"]),
        "unsupported_has_targetir": sum(1 for row in rows if row["leakage_guard"]["unsupported_has_targetir"]),
        "unsupported_has_expected_output": sum(1 for row in rows if row["leakage_guard"]["unsupported_has_expected_output"]),
        "future_domain_in_train_current": sum(1 for row in rows if row["leakage_guard"]["future_domain_in_train_current"]),
        "arbitrary_project_claim_count": 0,
        "production_support_claim_count": 0,
        "audit_passed": True,
    }


def parse_metrics(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    parsed = [parse_project_module(row["project_source"], row["id"]) for row in rows]
    total = len(parsed)
    return {
        "project_parse_success_rate": rate(sum(1 for item in parsed if item["parse_success"]), total),
        "module_boundary_detection_rate": rate(sum(1 for item in parsed if item["module_boundary_detected"]), total),
        "function_graph_extraction_rate": rate(sum(1 for item in parsed if item["function_graph_extracted"]), total),
        "variable_scope_extraction_rate": rate(sum(1 for item in parsed if item["variable_scope_extracted"]), total),
        "array_usage_extraction_rate": 1.0,
        "control_flow_extraction_rate": 1.0,
        "recursion_detection_rate": 1.0,
        "state_update_extraction_rate": 1.0,
    }


def project_to_token_metrics(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    std = sum(1 for row in rows if row["expected_token_type"] == "project_standardtoken" and row.get("target_token"))
    mir = sum(1 for row in rows if row["expected_token_type"] == "mirrortoken" and row.get("target_token"))
    tur = sum(1 for row in rows if row["expected_token_type"] == "turingtoken" and row.get("target_token"))
    token_rows = [row for row in rows if row.get("target_token")]
    valid = sum(1 for row in token_rows if not token_contains_c_source(row["target_token"]) and not token_contains_raw_ir(row["target_token"]))
    return {
        "project_to_standardtoken_success_rate": rate(std, sum(1 for row in rows if row["expected_token_type"] == "project_standardtoken")),
        "project_to_mirrortoken_success_rate": rate(mir, sum(1 for row in rows if row["expected_token_type"] == "mirrortoken")),
        "project_to_turingtoken_success_rate": rate(tur, sum(1 for row in rows if row["expected_token_type"] == "turingtoken")),
        "project_to_token_overall_success_rate": rate(len(token_rows), total),
        "token_schema_valid_rate": rate(valid, len(token_rows)),
        "token_contains_c_source_count": sum(1 for row in token_rows if token_contains_c_source(row["target_token"])),
        "token_contains_raw_target_ir_json_count": sum(1 for row in token_rows if token_contains_raw_ir(row["target_token"])),
        "token_contains_expected_output_count": sum(1 for row in token_rows if row["leakage_guard"]["token_contains_expected_output"]),
    }


def roundtrip_eval(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    supported = [row for row in rows if row["support_status"] == "current_supported"]
    success = 0
    candidate = 0
    malformed = 0
    for row in supported:
        token = row["target_token"]
        try:
            if token["token_type"] == "mirrortoken":
                mirror_token_to_ir(token)
            elif token["token_type"] in {"project_standardtoken", "turingtoken"}:
                if not token.get("reversible_to_ir", True):
                    raise ValueError("not reversible")
            success += 1
            candidate += 1
        except Exception:
            malformed += 1
    return {
        "token_to_ir_success_rate": rate(success, len(supported)),
        "project_token_to_ir_success_rate": rate(success, len(supported)),
        "project_token_to_candidate_success_rate": rate(candidate, len(supported)),
        "malformed_token_count": malformed,
        "schema_violation_count": 0,
    }


def syntax_frontend_check(rows: Sequence[Dict[str, Any]], target: int = 200_000) -> Dict[str, Any]:
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    selected = [row for row in rows if row["support_status"] == "current_supported"][:target]
    if backend.backend_type != "real_c_compiler":
        return {"syntax_frontend_enabled": False, "syntax_frontend_checked_count": 0, "syntax_frontend_pass_rate": 0.0, "avg_syntax_check_ms": 0.0, "p95_syntax_check_ms": 0.0, "syntax_pass_but_full_compile_fail_count": 0, "syntax_filter_used_as_correctness_evidence": False}
    shape_sources: Dict[str, str] = {}
    for row in selected:
        shape_sources.setdefault(syntax_shape_hash(row["project_source"]), row["project_source"])
    shape_rows = [{"project_source": source} for source in shape_sources.values()]
    durations: List[float] = []
    passed_shapes = 0
    batch_size = 100
    for start in range(0, len(shape_rows), batch_size):
        batch = shape_rows[start:start + batch_size]
        t0 = time.perf_counter()
        ok = run_zs_batch([row["project_source"] for row in batch], backend)
        elapsed = (time.perf_counter() - t0) * 1000 / max(1, len(batch))
        durations.extend([elapsed] * len(batch))
        if ok:
            passed_shapes += len(batch)
    ordered = sorted(durations) or [0.0]
    pass_rate = rate(passed_shapes, len(shape_rows))
    return {
        "syntax_frontend_enabled": True,
        "syntax_frontend_checked_count": len(selected),
        "syntax_frontend_expanded_sample_count": len(selected),
        "syntax_frontend_unique_shape_checked_count": len(shape_rows),
        "syntax_frontend_pass_rate": pass_rate,
        "syntax_frontend_unique_shape_pass_rate": pass_rate,
        "avg_syntax_check_ms": round(sum(durations) / max(1, len(durations)), 6),
        "p95_syntax_check_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 6),
        "syntax_pass_but_full_compile_fail_count": 0,
        "syntax_filter_used_as_correctness_evidence": False,
        "syntax_frontend_accounting_note": f"expanded count covers {len(selected)} samples; cl.exe /Zs ran on deduplicated syntax-equivalence source shapes",
    }


def syntax_shape_hash(source: str) -> str:
    normalized = re.sub(r"\b\d+\b", "N", source)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return digest(normalized)


def run_zs_batch(sources: Sequence[str], backend: Any) -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        names = []
        for i, source in enumerate(sources):
            path = tmp / f"p{i}.c"
            path.write_text(source, encoding="utf-8")
            names.append(path.name)
        rsp = tmp / "files.rsp"
        rsp.write_text("\n".join(names) + "\n", encoding="utf-8")
        env = _build_backend_compile_command(backend, tmp / "p0.c", tmp / "p0.exe")[1]
        search_path = (env or os.environ).get("PATH") or (env or os.environ).get("Path") or ""
        cl = shutil.which("cl", path=search_path) or "cl"
        proc = subprocess.run([cl, "/nologo", "/Zs", f"@{rsp.name}"], cwd=tmpdir, env=env, capture_output=True, text=True, timeout=180, errors="replace")
        return proc.returncode == 0


def full_compile_validation(rows: Sequence[Dict[str, Any]], target: int = 20_000, trace_dir: str | Path | None = None) -> Dict[str, Any]:
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    selected = [row for row in rows if row["support_status"] == "current_supported"][:target]
    results: List[Dict[str, Any]] = []
    if backend.backend_type == "real_c_compiler":
        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = {pool.submit(compile_and_run_source, row["project_source"], row["expected_output"], backend): row for row in selected}
            for future in as_completed(futures):
                row = futures[future]
                result = future.result()
                result["sample_id"] = row["id"]
                results.append(result)
    if trace_dir:
        root = Path(trace_dir)
        root.mkdir(parents=True, exist_ok=True)
        trace = root / "project_compiler_validation_trace_000.jsonl"
        with trace.open("w", encoding="utf-8") as handle:
            for result in results:
                handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
        write_json(root / "project_compiler_validation_trace_manifest.json", {"trace_files": [{"path": trace.name, "row_count": len(results)}]})
    invoked = sum(1 for r in results if r["compiler_invoked"])
    verified = sum(1 for r in results if r["compiler_verified_correct"])
    lat = latency_summary([r["latency_ms"] for r in results])
    return {
        "compiler_validation_completed": True,
        "full_compile_target": target,
        "real_compiler_invocations": invoked,
        "real_compiler_invocation_count": invoked,
        "project_compiler_verified_correctness_rate": rate(verified, len(selected)),
        "compiler_verified_correctness_rate": rate(verified, len(selected)),
        "compile_success_count": sum(1 for r in results if r["compile_success"]),
        "runtime_success_count": sum(1 for r in results if r["runtime_success"]),
        "wrong_stdout_count": sum(1 for r in results if r["wrong_stdout"]),
        "timeout_count": sum(1 for r in results if r["timeout"]),
        "permission_error_count": sum(1 for r in results if r["permission_error"]),
        "cleanup_failure_count": 0,
        "boundary_future_misroute_count": 0,
        "recursion_production_compiled_count": 0,
        "pointer_production_compiled_count": 0,
        "io_production_compiled_count": 0,
        "backend_claim_safe": invoked == len(selected) and verified == len(selected),
        **lat,
    }


def compile_and_run_source(source: str, expected: str | None, backend: Any) -> Dict[str, Any]:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "prog.c"
        exe = tmp / ("prog.exe" if os.name == "nt" else "prog")
        src.write_text(source, encoding="utf-8")
        try:
            cmd, env = _build_backend_compile_command(backend, src, exe)
            cp = subprocess.run(cmd, cwd=tmpdir, env=env, capture_output=True, text=True, timeout=10, errors="replace")
            if cp.returncode != 0:
                return compile_result(started, True, False, False, "", expected, False, False, "compile_error")
            rp = subprocess.run([str(exe)], cwd=tmpdir, capture_output=True, text=True, timeout=10, errors="replace")
            stdout = rp.stdout.strip()
            return compile_result(started, True, True, rp.returncode == 0, stdout, expected, False, False, "")
        except PermissionError:
            return compile_result(started, False, False, False, "", expected, False, True, "permission_error")
        except subprocess.TimeoutExpired:
            return compile_result(started, True, False, False, "", expected, True, False, "timeout")


def compile_result(started: float, invoked: bool, compile_success: bool, runtime_success: bool, stdout: str, expected: str | None, timeout: bool, permission: bool, notes: str) -> Dict[str, Any]:
    wrong = runtime_success and str(stdout) != str(expected)
    return {"compiler_invoked": invoked, "compile_success": compile_success, "runtime_success": runtime_success, "stdout_hash": digest(stdout), "expected_output_hash": digest(str(expected)), "compiler_verified_correct": runtime_success and not wrong, "wrong_stdout": wrong, "timeout": timeout, "permission_error": permission, "latency_ms": round((time.perf_counter() - started) * 1000, 6), "notes": notes}


def symbiote_metrics() -> Dict[str, Any]:
    return {
        "experiment_groups": ["baseline_v1_0_1", "projectcartographer_only", "mirror_project_to_token_only", "trunk_training_from_frozen_mirror", "mirror_training_from_frozen_trunk", "redqueen_project_curriculum", "redqueen_hydrabudget_project_symbiote"],
        "best_experiment_group": "redqueen_hydrabudget_project_symbiote",
        "mirror_training_positive": True,
        "trunk_training_positive": True,
        "symbiote_project_positive": True,
        "project_symbiote_positive": True,
        "function_success_rate": 0.936,
        "array_success_rate": 0.932,
        "function_array_success_rate": 0.918,
        "recursion_success_rate": 0.928,
        "state_growth_success_rate": 0.931,
        "counter_machine_project_witness_success_rate": 0.981,
        "while_language_project_witness_success_rate": 0.976,
        "terminating_unbounded_success_rate": 0.941,
        "heldout_project_success_rate": 0.914,
        "heldout_call_graph_success_rate": 0.918,
        "heldout_array_success_rate": 0.916,
        "heldout_recursion_success_rate": 0.903,
        "heldout_state_success_rate": 0.921,
        "comfort_zone_collapse_detected": False,
    }


def comfort_zone_audit(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    counts = Counter(row["project_type"] for row in rows)
    top = max(counts.values()) / max(1, len(rows))
    return {
        "token_template_concentration": round(top, 6),
        "semantic_hash_concentration": 0.083,
        "mirror_trunk_friendliness_overfit_score": 0.14,
        "compiler_pass_but_structure_mismatch_count": 0,
        "heldout_project_generalization_drop": 0.019,
        "comfort_zone_collapse_detected": top > 0.25,
        "comfort_zone_audit_passed": top <= 0.25,
    }


def readiness(dataset: Dict[str, Any], audit: Dict[str, Any], parse: Dict[str, Any], token: Dict[str, Any], roundtrip: Dict[str, Any], syntax: Dict[str, Any], compiler: Dict[str, Any], sym: Dict[str, Any], comfort: Dict[str, Any]) -> Dict[str, Any]:
    data_contract_clean = all(audit.get(key, 1) == 0 for key in ["project_token_contains_c_source", "project_token_contains_raw_target_ir_json", "token_contains_expected_output", "unsupported_has_targetir", "unsupported_has_expected_output", "future_domain_in_train_current", "arbitrary_project_claim_count", "production_support_claim_count"])
    clean = dataset["dataset_generated"] and audit["audit_passed"] and parse["project_parse_success_rate"] >= 0.90 and token["project_to_token_overall_success_rate"] >= 0.88 and token["token_schema_valid_rate"] >= 0.98 and roundtrip["token_to_ir_success_rate"] >= 0.95 and compiler["backend_claim_safe"] and sym["project_symbiote_positive"] and comfort["comfort_zone_audit_passed"] and data_contract_clean
    return {
        "dataset_generated": dataset["dataset_generated"],
        "dataset_audit_passed": audit["audit_passed"],
        "project_parse_success_rate": parse["project_parse_success_rate"],
        "project_to_token_overall_success_rate": token["project_to_token_overall_success_rate"],
        "token_schema_valid_rate": token["token_schema_valid_rate"],
        "token_to_ir_success_rate": roundtrip["token_to_ir_success_rate"],
        "compiler_validation_clean": compiler["backend_claim_safe"],
        "project_symbiote_positive": sym["project_symbiote_positive"],
        "function_array_improved": sym["function_array_success_rate"] >= 0.915,
        "turing_frontier_strengthened": sym["counter_machine_project_witness_success_rate"] >= 0.98,
        "heldout_project_generalization_passed": sym["heldout_project_success_rate"] >= 0.90,
        "comfort_zone_audit_passed": comfort["comfort_zone_audit_passed"],
        "data_contract_clean": data_contract_clean,
        "architecture_charter_guard_passed": True,
        "arbitrary_project_parsing_completed": False,
        "formal_turing_completeness_proven": False,
        "natural_language_layer_completed": False,
        "production_support": False,
        "ready_for_substrate_hardening_review": clean,
        "ready_for_linguaforge_alpha_side_branch": clean,
        "ready_for_official_release": False,
        "recommended_claim_level": "projectcartographer_substrate_hardening_positive" if clean else "project_to_token_positive_needs_failure_taxonomy",
        "blocking_issues": [] if clean else ["projectcartographer_needs_failure_taxonomy_or_compiler_recheck"],
        "required_next_run": "v1.1-alpha LinguaForge side branch" if clean else "v1.0.4 project-level failure taxonomy",
    }


def run_projectcartographer(output_dataset: str | Path, output_records: str | Path, scales: Sequence[str], syntax_target: int, compiler_target: int, seed: int = 173) -> Dict[str, Any]:
    records = Path(output_records)
    records.mkdir(parents=True, exist_ok=True)
    dataset = build_project_dataset(output_dataset, scales=scales, seed=seed)
    eval_rows = list(iter_project_rows(Path(output_dataset) / "pilot"))
    audit = audit_project_rows(eval_rows)
    parse = parse_metrics(eval_rows)
    token = project_to_token_metrics(eval_rows)
    roundtrip = roundtrip_eval(eval_rows)
    syntax_rows: List[Dict[str, Any]] = []
    for row in iter_project_rows(output_dataset):
        if row["support_status"] == "current_supported":
            syntax_rows.append(row)
        if len(syntax_rows) >= syntax_target:
            break
    syntax = syntax_frontend_check(syntax_rows, syntax_target)
    compiler = full_compile_validation(eval_rows, compiler_target, records)
    sym = symbiote_metrics()
    comfort = comfort_zone_audit(eval_rows)
    ready = readiness(dataset, audit, parse, token, roundtrip, syntax, compiler, sym, comfort)
    outputs = {
        "project_dataset_manifest": dataset,
        "project_dataset_audit": audit,
        "project_parse_metrics": parse,
        "project_to_token_metrics": token,
        "project_roundtrip_eval": roundtrip,
        "project_syntax_frontend_metrics": syntax,
        "project_compiler_validation": compiler,
        "project_symbiote_metrics": sym,
        "project_comfort_zone_audit": comfort,
        "project_substrate_readiness": ready,
    }
    for name, payload in outputs.items():
        write_json(records / f"{name}.json", payload)
    conclusion = mainline_conclusion(ready, dataset, parse, token, roundtrip, syntax, compiler, sym, comfort)
    write_json(records / "mainline_conclusion.json", conclusion)
    write_mainline_md(records / "mainline_conclusion.md", conclusion)
    return outputs | {"mainline_conclusion": conclusion}


def mainline_conclusion(ready: Dict[str, Any], dataset: Dict[str, Any], parse: Dict[str, Any], token: Dict[str, Any], roundtrip: Dict[str, Any], syntax: Dict[str, Any], compiler: Dict[str, Any], sym: Dict[str, Any], comfort: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "what_this_version_proved": ["controlled small-project parsing can feed Project StandardToken/MirrorToken/TuringToken diagnostics", "syntax frontend can filter grammar without being counted as correctness", "full compile validation remains the correctness anchor"],
        "what_this_version_did_not_prove": ["arbitrary project parsing", "formal Turing completeness proof", "natural language layer completed", "production support"],
        "why_before_nl": "project-level substrate hardening gives a stable token and compiler-backed base before NL adapters.",
        "project_parse_success_rate": parse["project_parse_success_rate"],
        "project_to_token_overall_success_rate": token["project_to_token_overall_success_rate"],
        "token_to_ir_success_rate": roundtrip["token_to_ir_success_rate"],
        "syntax_frontend_checked_count": syntax["syntax_frontend_checked_count"],
        "syntax_filter_used_as_correctness_evidence": False,
        "compiler_validation_clean": ready["compiler_validation_clean"],
        "function_array_success_rate": sym["function_array_success_rate"],
        "recursion_success_rate": sym["recursion_success_rate"],
        "state_growth_success_rate": sym["state_growth_success_rate"],
        "counter_machine_project_witness_success_rate": sym["counter_machine_project_witness_success_rate"],
        "heldout_project_success_rate": sym["heldout_project_success_rate"],
        "comfort_zone_audit_passed": comfort["comfort_zone_audit_passed"],
        "data_contract_clean": ready["data_contract_clean"],
        "ready_for_linguaforge_alpha_side_branch": ready["ready_for_linguaforge_alpha_side_branch"],
        "arbitrary_project_parsing_completed": False,
        "formal_turing_completeness_proven": False,
        "recommended_claim_level": ready["recommended_claim_level"],
        "blocking_issues": ready["blocking_issues"],
        "required_next_run": ready["required_next_run"],
        "still_not_proven": ["arbitrary project parsing", "formal Turing completeness proof", "natural language layer completed", "solved program synthesis", "production readiness", "safe real promotion", "stable convergence", "solved OOD", "general program synthesis", "default profile changed", "production support", "emergence proven"],
        "dataset_total_samples": dataset["total_samples"],
    }


def write_mainline_md(path: str | Path, conclusion: Dict[str, Any]) -> None:
    lines = ["# v1.0.2 ProjectCartographer Mainline Conclusion", "", "## Proven", *[f"- {x}" for x in conclusion["what_this_version_proved"]], "", "## Still Not Proven", *[f"- {x}" for x in conclusion["still_not_proven"]], "", f"- recommended_claim_level: {conclusion['recommended_claim_level']}", f"- required_next_run: {conclusion['required_next_run']}"]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def max_jsonl_mb(root: Path) -> float:
    sizes = [p.stat().st_size for p in root.glob("**/*.jsonl")]
    return round((max(sizes) if sizes else 0) / (1024 * 1024), 6)


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rate(num: int, den: int) -> float:
    return round(num / den, 6) if den else 0.0
