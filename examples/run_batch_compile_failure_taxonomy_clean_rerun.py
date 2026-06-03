import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.batch_compile_failure_taxonomy_clean_rerun import main


if __name__ == "__main__":
    main()
