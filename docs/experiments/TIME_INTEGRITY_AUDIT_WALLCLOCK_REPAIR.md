# Time Integrity Audit and Wall-clock Repair

## 1. Why this version exists

v1.0.8.6 claimed 8 hours, but the observed task duration may have been around 40 minutes. This version audits whether actual wall-clock time was measured correctly.

## 2. What this version does

- audits v1.0.8.6 time records
- scans code for planned-as-actual wall-clock bugs
- separates `planned_wall_clock_hours` from `actual_wall_clock_hours`
- adds monotonic timing
- adds cycle-level timing
- adds heartbeat timing
- repairs readiness rules
- reruns a real 2-hour wall-clock validation

## 3. What this version does not do

This version does not claim:

- production function support completed
- production array support completed
- production recursion support completed
- RedQueen autonomous governance completed
- v1.0.8.6 true 8-hour validation confirmed, unless evidence supports it
- production readiness
- official release

## 4. Time honesty rule

Actual wall-clock must come from `time.monotonic()` or an equivalent monotonic source.

The following are invalid as actual elapsed time:

- `args.wall_clock_min_hours`
- `cycles * cycle_min_hours`
- planned duration
- target duration
- padded summary value
- fake sleep without validation work
