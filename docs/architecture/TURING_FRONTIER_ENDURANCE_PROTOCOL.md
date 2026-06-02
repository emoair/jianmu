# Turing Frontier Endurance Protocol

The v0.9.26.1 endurance protocol requires wall_clock_min_hours = 12 and rolling_window_count >= 24 before endurance_completed may be true. Early completion of sample targets, compiler validation, or metric targets does not complete the run.

If wall_clock_hours is below 12, the run must report endurance_completed = false, partial = true, and partial_reason = wall_clock_below_minimum. The audit records start_timestamp, end_timestamp, wall_clock_hours, checkpoint_count, resume_count, rolling_window_count, and whether execution continued after sample target completion.

Checkpoint/resume records real elapsed wall-clock time. Resume increments resume_count and must not fabricate missing time.
