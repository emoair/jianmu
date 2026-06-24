# Mirror Freeze State Machine Contract

Valid states are:

- `LANE_A_ACTIVE_LANE_B_FROZEN`
- `LANE_B_ACTIVE_LANE_A_FROZEN`
- `BOTH_FROZEN_REVIEW_ONLY`

`INVALID_BOTH_ACTIVE` must be rejected. Frozen mutation must be rejected. Lane swap must be explicit. Default profile reachability must remain false.

