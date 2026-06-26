# Idle Padding Detection Contract

Validation may not satisfy wall-clock requirements by idling after backend work stops. Active validation phases must reject repeated zero-delta backend windows, stale last-backend age, and early target completion without continued heldout, replay, boundary, or backend work.
