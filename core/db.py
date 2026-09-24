"""Unified database access layer.

The whole project talks to the database through this module, so switching
between local SQLite and cloud Postgres is a single environment variable
(DB_URL); no code changes anywhere else.
"""
from __future__ import annotations

import json
from functools import lru_cache

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import DB_URL, ROOT


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(
        DB_URL,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
    )


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


# --------------------------------------------------------------------------
# PostgreSQL: views block table replacement.
#
# pandas' to_sql(if_exists="replace") issues DROP TABLE, which PostgreSQL
# refuses while any view depends on the table. Before a rebuild we save the
# definition of every view in the schema (including ones created by hand, e.g.
# for Power BI), drop them, and recreate them once the tables are back.
# SQLite does not enforce this, so both functions are no-ops there.
# --------------------------------------------------------------------------
SAVED_VIEWS = ROOT / "artifacts" / "saved_views.json"


def save_and_drop_views(schema: str = "public") -> list[str]:
    if dialect() != "postgresql":
        return []
    views = read_sql(
        "SELECT viewname, definition FROM pg_views WHERE schemaname = :s ORDER BY viewname", s=schema)
    if not len(views):
        return []
    saved = {r.viewname: r.definition for r in views.itertuples()}
    # Merge with any definitions saved by an earlier, interrupted build.
    if SAVED_VIEWS.exists():
        saved = {**json.loads(SAVED_VIEWS.read_text()), **saved}
    SAVED_VIEWS.write_text(json.dumps(saved, indent=2))
    with get_engine().begin() as conn:
        for name in views.viewname:
            conn.execute(text(f'DROP VIEW IF EXISTS "{schema}"."{name}" CASCADE'))
    return list(views.viewname)


def restore_views(schema: str = "public") -> list[str]:
    """Recreate saved views that do not exist yet. Views that depend on other
    views are retried until no further progress is possible."""
    if dialect() != "postgresql" or not SAVED_VIEWS.exists():
        return []
    pending = json.loads(SAVED_VIEWS.read_text())
    existing = set(read_sql("SELECT viewname FROM pg_views WHERE schemaname = :s", s=schema).viewname)
    pending = {k: v for k, v in pending.items() if k not in existing}
    restored, errors = [], {}
    while pending:
        progress = False
        for name, definition in list(pending.items()):
            try:
                with get_engine().begin() as conn:
                    conn.execute(text(f'CREATE VIEW "{schema}"."{name}" AS {definition}'))
                restored.append(name)
                del pending[name]
                progress = True
            except Exception as exc:  # dependency not ready yet, or a column changed
                errors[name] = str(exc).splitlines()[0]
        if not progress:
            break
    if pending:
        print("WARNING: could not restore these views (definitions kept in "
              f"{SAVED_VIEWS.name}):")
        for name in pending:
            print(f"  {name}: {errors.get(name, 'unknown error')}")
    else:
        SAVED_VIEWS.unlink(missing_ok=True)
    return restored