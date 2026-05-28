# Progress Repair and Plateau Diagnosis

v0.9.8.1 exists because v0.9.8 reproduced the bounded substrate signal but did not improve heldout success over v0.9.7, and its terminal progress UI emitted only a few phase-boundary events. This version repairs progress visibility and diagnoses the v0.9.8 plateau without changing the main architecture.

Progress is only an observation tool. JSON and JSONL records remain the evidence. Progress output must not change metrics, replace records, hide exceptions, or become a proof of model capability.

The plateau diagnosis separates candidate miss, in-beam wrong top1, stage-specific weakness, beam-size bottleneck, baseline/ablation bottleneck, and scorer/router/root-colony/nutrient-toxic memory bottlenecks. Beam sweep results are diagnostic only and do not replace the v0.9.8 beam-size-8 mainline result.

Non-claims: no Turing completeness, no solved arithmetic, no solved program synthesis, no stable convergence, no solved OOD, no safe real promotion, and no production readiness.

