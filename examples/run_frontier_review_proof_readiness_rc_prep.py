from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.frontier_review_proof_readiness_rc_prep import main


if __name__ == "__main__":
    raise SystemExit(main())
