# RedQueen Multi-round Response Contract

The multiround validation uses five cycles:

- Cycle 0: baseline, no weak signal
- Cycle 1: function weak signal
- Cycle 2: function response plus mixed weak signal
- Cycle 3: function signal removed, mixed signal remains
- Cycle 4: all weak signals removed

The expected response is bounded: weak categories should receive increased sample push and active review, stable recursion should not be falsely marked weak, and removed weak signals should anneal gradually.

Overreaction and underreaction both block a positive readiness result.
