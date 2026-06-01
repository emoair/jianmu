# Longhaul Wall-Clock Rule

All longhaul, endurance, and sustained-test tasks must record real start_timestamp, end_timestamp, and wall_clock_hours.

Rules:

- wall_clock_min_hours = 6.
- max_runtime_hours = 12 unless the task explicitly sets another cap.
- If sample targets finish early, the run must continue into another rolling window or endurance cycle.
- If wall_clock_hours < 6, set longhaul_completed or endurance_completed to false, set partial to true, and use partial_reason = "wall_clock_below_minimum".
- Sample completion alone cannot be reported as longhaul completion.

This rule applies to future tasks using longhaul, endurance, or sustained-test wording.
