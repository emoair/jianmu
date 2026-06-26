# v1.0.8.8.3 OPT Active Work Rate and Git Residual Process Repair

## 1. Why this version exists

v1.0.8.8.2 restored OPT output and true backend validation, but the displayed progress did not clearly prove active backend work across time. Backend counts could reach a target while progress lines continued, so this version audits whether progress lines reflect live backend compiler work.

Git for Windows residual processes were also observed, likely related to Git or IDE scanning of large records and trace shards.

## 2. What this version does

- Audits active backend work distribution.
- Adds delta, rate, last-active-age, active ratio, Git process count, RSS, and queue fields to OPT progress.
- Detects idle padding and cumulative-only OPT output.
- Verifies OPT trace against backend manifests.
- Detects scripted or too-perfect summary output.
- Repairs Git residual process cleanup and records root-cause evidence.
- Enforces trace shard size caps.
- Runs short active backend validation.

## 3. What this version does not do

This version does not claim production support completed, RedQueen autonomous governance completed, official release, v1.0.8.8 old compiler claim restored, or a new 8h backend stability rerun.

## 4. Active progress rule

OPT progress is valid only when it reports cumulative backend counts, deltas since the previous progress line, backend rate, last backend invocation age, active or idle state, idle windows, active backend window ratio, current validation phase, and evidence that backend work continues after early targets.
