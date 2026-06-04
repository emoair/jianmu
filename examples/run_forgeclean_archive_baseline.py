from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.archive_index_builder import main


if __name__ == "__main__":
    raise SystemExit(main())
