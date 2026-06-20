# Post-run Idle Sentinel Contract

The post-run idle sentinel waits for a grace period after validation completes, then checks child processes, git processes, compiler processes, generated executable processes, worker threads, manifest handles, git index locks, and temp-dir collisions.

A clean sentinel is required before RedQueen iteration 2.
