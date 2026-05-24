# v0.9.3 Arithmetic Training Probe Report

## Scope

This run is a bounded arithmetic training probe on the v0.9.2 arithmetic curriculum dataset. It does not claim solved arithmetic.

## No-Label Free-Beam Result

- supported_candidate_hit_before: 0.8
- supported_candidate_hit_after: 0.95
- supported_correct_output_in_beam_before: 0.8
- supported_correct_output_in_beam_after: 0.95
- forbidden_field_access_count: 0

## Boundary Result

- unsupported_false_accept_rate: 0.0
- trap_false_accept_rate: 0.0
- future_domain_supported_accept_rate: 0.0
- near_ood_supported_accept_rate: 0.0
- division_by_zero_false_accept_rate: 0.0
- non_integer_division_false_accept_rate: 0.0

## Full-State Reload

- persisted_state_support_level: full_router_root
- missing_for_full_state: []
- cross_process_reload_passed: True

## Non-Claims

- no solved arithmetic
- no stable convergence
- no solved OOD
- no same-size LLM advantage
- no safe real promotion
