"""Test configuration.

Points DB_URL at a throw-away SQLite file BEFORE any project module is
imported. core.config calls load_dotenv(), which would otherwise pick up the
production Neon/Postgres URL from .env; tests must never write there.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_TMP = Path(tempfile.mkdtemp(prefix="bredgepulse_test_"))
os.environ["DB_URL"] = f"sqlite:///{_TMP / 'test.sqlite'}"
