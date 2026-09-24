"""Recreate any database views saved by etl/load.py (PostgreSQL only).

The analytics marts are rebuilt by persist_model_outputs.py; this step brings
back every other view that existed before the build, e.g. views created by
hand for Power BI, exactly as they were defined.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.db import restore_views, dialect


def main() -> None:
    if dialect() != "postgresql":
        print("SQLite: nothing to restore")
        return
    restored = restore_views()
    print(f"Restored {len(restored)} views" + (": " + ", ".join(restored) if restored else ""))


if __name__ == "__main__":
    main()