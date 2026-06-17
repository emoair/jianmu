# Replay Concurrency Repair Contract

Replay repair must keep replay workers at 16 when requested. It must not silently downgrade to a single worker.

The replay path uses a shard index, per-worker assignment, per-sample temp directories, sharded output manifests, aggregate-only accounting locks, worker heartbeat, timeout classification, and duplicate sample ID detection.

If 16-worker replay fails, readiness must report replay concurrency still blocked or partial; it must not report a positive result by rerunning single-worker replay as a substitute.
