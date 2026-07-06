# Memory Lifecycle Contract

Actual memory evidence must include RSS/USS availability, tracemalloc heap, gc object count, queue sizes, writer buffers, and post-cleanup snapshots. Allocator high-water must be distinguished from live-object leak.
