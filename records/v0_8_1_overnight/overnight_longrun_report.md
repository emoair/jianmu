# v0.8.1 Overnight Full/Longrun Probe??????????

## Modes Attempted??????

Requested order: xlarge, full, longrun.

Script-internal records also include large as the baseline scale for the v0.8.1 long-run probe.

## Modes Completed / Partial / Skipped???/??/???

- xlarge: completed=True, partial=False, runtime_seconds=901.4492
- full: completed=False, skip_reason=full skipped by bounded runtime policy（受限运行时间策略跳过 full）
- longrun: completed=False, skip_reason=longrun skipped by bounded runtime policy（受限运行时间策略跳过 longrun）

## Runtime Cost??????

- recorded total runtime seconds, including script-internal large baseline: 1370.7531
- xlarge runtime seconds: 901.4492
- full runtime seconds: 0.0
- longrun runtime seconds: 0.0

## Global Beam Trend???????

- large global_correct_targetir_in_beam_rate: 0.5017
- xlarge global_correct_targetir_in_beam_rate: 0.8167

## Candidate Space Failure????????

- large candidate_space_failure_rate: 0.4983
- xlarge candidate_space_failure_rate: 0.1833

## Root Lifecycle Scale?????????

- large stable_root_count: 1239
- xlarge stable_root_count: 4739
- xlarge replacement_root_count: 1600
- xlarge necrotic_archived_count: 1661

## OOD Toxicity???????

- xlarge ood_false_accept_after_shadow: 0.335
- guard ood_false_accept_before_guard: 0.335
- guard ood_false_accept_after_guard: 0.23500000000000001

## Guard Candidate Stability?????????

- guard_candidate_count: 4
- guard_candidate_accepted_count: 2
- guard_candidate_rollback_count: 2
- arithmetic_supported_retention_after_guard: 1.0
- global_beam_after_guard: 0.5017

## Bottleneck Diagnosis??????

The xlarge run strengthened the scale signal: global beam improved and candidate-space failure decreased relative to large. OOD false accept still remained materially present, and guard candidates reduced OOD false accept without reducing arithmetic retention in the recorded guard balance.

full and longrun were not completed; they were skipped by the existing bounded runtime policy, and this report does not treat them as completed.

## Non-Claims?????

This overnight scale stress does not prove stable convergence, general program synthesis, solved arithmetic, or safe real promotion. Real promotion remained disabled.
