# Train Heldout Backend Validation Separation Contract

Train, heldout, replay, and negative boundary lanes must remain separate. Training samples may not count as heldout validation, heldout samples may not update training weights, replay samples must not duplicate train samples, and negative boundary samples must not become positive training evidence.
