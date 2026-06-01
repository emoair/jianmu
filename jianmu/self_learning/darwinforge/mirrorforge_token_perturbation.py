from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.darwinforge.mirrorforge_abstraction_variants import make_variant_token


PERTURBATIONS = [
    "synonym_token_replacement",
    "variable_renaming",
    "harmless_local_reorder",
    "expanded_structured_form",
    "compressed_one_line_form",
    "separator_variation",
    "equivalent_phrase_token",
    "minor_noise_token",
]


def perturb_mirror_token(mirror_token: Dict[str, Any], perturbation: str) -> Dict[str, Any]:
    if perturbation not in PERTURBATIONS:
        raise ValueError(f"unknown perturbation: {perturbation}")
    if perturbation in {"synonym_token_replacement", "equivalent_phrase_token"}:
        token = make_variant_token(mirror_token, "noisy")
    elif perturbation == "compressed_one_line_form":
        token = make_variant_token(mirror_token, "compressed")
    elif perturbation == "expanded_structured_form":
        token = make_variant_token(mirror_token, "semantic")
        token["token_text"] = "\n".join(token["token_sequence"])
    else:
        token = dict(mirror_token)
        token["normalized_token_sequence"] = list(mirror_token["token_sequence"])
        token["token_text"] = token["token_text"].replace(" ", "  |  ") if perturbation == "separator_variation" else token["token_text"]
    token["perturbation"] = perturbation
    token["semantic_preserving"] = True
    return token
