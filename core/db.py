"""Unified database access layer.

The whole project talks to the database through this module, so switching
between local SQLite and cloud Postgres is a single environment variable
(DB_URL) — no code changes anywhere else.
"""
from __future__ import annotations

from functools import lru_cache

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import DB_URL, ROOT


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(DB_URL, future=True)


def dialect() -> str:
    return get_engine().dialect.name  # 'sqlite' or 'postgresql'


def read_sql(query: str, **params) -> pd.DataFrame:
    """Run a SELECT. Use named params (:name) for portability across dialects."""
    return pd.read_sql_query(text(query), get_engine(), params=params or None)


def exec_sql(query: str, **params) -> None:
    with get_engine().begin() as conn:
        conn.execute(text(query), params)


def write_df(df: pd.DataFrame, table: str, if_exists: str = "replace") -> None:
    df.to_sql(table, get_engine(), if_exists=if_exists, index=False)


def create_views() -> None:
    """Create the analytics marts for the active dialect."""
    fname = ("analytics_views_sqlite.sql" if dialect() == "sqlite"
             else "analytics_views.sql")
    sql = (ROOT / "database" / "marts" / fname).read_text()
    with get_engine().begin() as conn:
        for stmt in sql.split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
