from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.codecartographer_supported_subset import classify_supported_subset, feature_flags_from_code


FUNCTION_RE = re.compile(r"int\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\((?P<args>[^)]*)\)\s*\{", re.MULTILINE)


def parse_code_module(source: str | Path, module_name: str | None = None) -> Dict[str, Any]:
    if isinstance(source, Path) or (isinstance(source, str) and "\n" not in source and "{" not in source and Path(source).exists()):
        path = Path(source)
        code = path.read_text(encoding="utf-8")
        module_name = module_name or path.stem
        source_path = str(path)
    else:
        code = str(source)
        module_name = module_name or "inline_module"
        source_path = None
    features = feature_flags_from_code(code)
    classification = classify_supported_subset(features)
    functions = _functions(code)
    return {
        "parse_success": True,
        "module_name": module_name,
        "source_path": source_path,
        "source_code": code,
        "functions": functions,
        "features": features,
        "classification": classification,
        "parse_errors": [],
    }


def _functions(code: str) -> List[Dict[str, Any]]:
    matches = list(FUNCTION_RE.finditer(code))
    result = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(code)
        body = code[start:end].rsplit("}", 1)[0]
        result.append({
            "name": match.group("name"),
            "args": [arg.strip() for arg in match.group("args").split(",") if arg.strip() and arg.strip() != "void"],
            "return_type": "int",
            "body": body,
            "local_int_variables": re.findall(r"\bint\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|\[|;)", body),
            "return_expressions": re.findall(r"\breturn\s+([^;]+);", body),
        })
    if not result:
        result.append({"name": "compute", "args": [], "return_type": "int", "body": code, "local_int_variables": [], "return_expressions": ["0"]})
    return result
