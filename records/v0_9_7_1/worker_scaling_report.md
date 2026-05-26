# Bounded Substrate Worker Scaling

best_worker_count_for_bounded_substrate: 32
recommended_default_worker_count: 32

- 8: sps=0.176172, stable=True, p95=5666.5308
- 16: sps=1.986689, stable=True, p95=499.7164
- 32: sps=2.057355, stable=True, p95=482.057
- 64: sps=1.148327, stable=True, p95=867.4752

Partial sample count reason: sample count below 500; bounded by local process-spawn stability/runtime after 16-worker validation produced PermissionError failures
