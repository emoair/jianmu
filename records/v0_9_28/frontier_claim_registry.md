# Frontier Claim Registry

## Allowed/Blocked Claims
{
  "claims": [
    {
      "claim": "function/array frontier clean review-ready",
      "allowed": true,
      "evidence_paths": [
        "records/v0_9_28/function_array_frontier_review.json"
      ],
      "safe_wording": "Function/array frontier evidence is review-ready under diagnostic boundaries.",
      "unsafe_wording": "Function/array production support is complete.",
      "overclaim_risk": "medium"
    },
    {
      "claim": "Turing frontier clean review-ready",
      "allowed": true,
      "evidence_paths": [
        "records/v0_9_28/turing_frontier_review.json"
      ],
      "safe_wording": "Turing frontier constructive evidence is review-ready.",
      "unsafe_wording": "Formal Turing completeness is proven.",
      "overclaim_risk": "high"
    },
    {
      "claim": "constructive Turing expressivity evidence completed",
      "allowed": true,
      "evidence_paths": [
        "records/v0_9_28/proof_artifact_review/proof_readiness.json"
      ],
      "safe_wording": "Constructive counter-machine and WHILE-language mappings are documented.",
      "unsafe_wording": "Finite validation proves Turing completeness.",
      "overclaim_risk": "high"
    },
    {
      "claim": "compiler-backed clean validation evidence",
      "allowed": true,
      "evidence_paths": [
        "records/v0_9_27_1/batch_compile_clean_validation.json"
      ],
      "safe_wording": "20K prior full compile validation is clean; 50K continuation is partial unless new invocations are run.",
      "unsafe_wording": "50K clean validation completed.",
      "overclaim_risk": "medium"
    },
    {
      "claim": "ready_for_v1_0_rc1_branch",
      "allowed": true,
      "evidence_paths": [
        "records/v0_9_28/frontier_review_readiness.json"
      ],
      "safe_wording": "Ready to prepare an RC1 branch after human review with conservative wording.",
      "unsafe_wording": "v1.0 release completed.",
      "overclaim_risk": "medium"
    },
    {
      "claim": "formal Turing completeness proven",
      "allowed": false,
      "evidence_paths": [
        "records/v0_9_28/proof_artifact_review/proof_boundary_notice.md"
      ],
      "safe_wording": "Formal Turing completeness remains unproven.",
      "unsafe_wording": "Formal Turing completeness proven.",
      "overclaim_risk": "blocking"
    }
  ],
  "forbidden_claims_blocked": [
    "production readiness",
    "solved program synthesis",
    "function/array production support",
    "recursion production support",
    "arbitrary project parsing",
    "natural language layer completed",
    "v1.0 release completed"
  ],
  "no_claim_overreach_detected": true
}
