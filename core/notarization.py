"""Governance: a blockchain-inspired decision-notarization ledger.

Module 7 (Data Governance) covers Data Notarization via blockchain. A full
distributed ledger is overkill for a single-organisation audit trail — what
Bredge actually needs is the *property* a blockchain gives you: that a past
record cannot be silently altered or deleted without detection. A SHA-256
hash chain gives exactly that property with no new infrastructure.

Every governed event (a model run, an intervention logged, an outcome
closed) is appended as a row whose hash depends on its own content AND the
hash of the row before it. Tampering with, or deleting, any past row changes
every hash after it — so `verify_chain()` can prove, on demand, whether the
full history is intact.

Usage:
    from core.notarization import notarize, verify_chain, ledger_tail
    notarize("intervention_logged", engagement_id, {"owner": ..., "type": ...})
    verify_chain()   -> {"ok": True, "checked": 45, "broken_at": None}
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from core.db import read_sql, exec_sql, dialect

GENESIS = "0" * 64


def _ensure_table() -> None:
    if dialect() == "sqlite":
        ddl = """
        CREATE TABLE IF NOT EXISTS governance_ledger (
            ledger_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT NOT NULL,
            event_type  TEXT NOT NULL,
            ref_id      TEXT,
            payload     TEXT NOT NULL,
            prev_hash   TEXT NOT NULL,
            record_hash TEXT NOT NULL
        )"""
    else:
        ddl = """
        CREATE TABLE IF NOT EXISTS governance_ledger (
            ledger_id   SERIAL PRIMARY KEY,
            ts          VARCHAR(40) NOT NULL,
            event_type  VARCHAR(40) NOT NULL,
            ref_id      VARCHAR(64),
            payload     TEXT NOT NULL,
            prev_hash   CHAR(64) NOT NULL,
            record_hash CHAR(64) NOT NULL
        )"""
    exec_sql(ddl)


def _canonical(obj) -> str:
    """Deterministic JSON so the same content always hashes the same way."""
    return json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))


def _last_hash() -> str:
    row = read_sql("SELECT record_hash FROM governance_ledger ORDER BY ledger_id DESC LIMIT 1")
    return row.iloc[0]["record_hash"] if len(row) else GENESIS


def notarize(event_type: str, ref_id: str, payload: dict) -> dict:
    """Append one tamper-evident record to the ledger. Returns the stored record."""
    _ensure_table()
    prev = _last_hash()
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    body = _canonical({"ts": ts, "event_type": event_type, "ref_id": ref_id,
                        "payload": payload, "prev_hash": prev})
    record_hash = hashlib.sha256(body.encode()).hexdigest()
    exec_sql("""
        INSERT INTO governance_ledger (ts, event_type, ref_id, payload, prev_hash, record_hash)
        VALUES (:ts, :event_type, :ref_id, :payload, :prev_hash, :record_hash)
    """, ts=ts, event_type=event_type, ref_id=str(ref_id), payload=_canonical(payload),
         prev_hash=prev, record_hash=record_hash)
    return {"ts": ts, "event_type": event_type, "ref_id": ref_id,
            "record_hash": record_hash, "prev_hash": prev}


def verify_chain() -> dict:
    """Recompute every hash from genesis and confirm the stored chain is unbroken.

    Returns {"ok": bool, "checked": int, "broken_at": ledger_id | None}.
    """
    _ensure_table()
    rows = read_sql("SELECT * FROM governance_ledger ORDER BY ledger_id ASC")
    prev = GENESIS
    for i, r in rows.iterrows():
        body = _canonical({"ts": r["ts"], "event_type": r["event_type"], "ref_id": r["ref_id"],
                            "payload": json.loads(r["payload"]), "prev_hash": prev})
        expected = hashlib.sha256(body.encode()).hexdigest()
        if r["prev_hash"] != prev or r["record_hash"] != expected:
            return {"ok": False, "checked": int(i), "broken_at": int(r["ledger_id"])}
        prev = r["record_hash"]
    return {"ok": True, "checked": int(len(rows)), "broken_at": None}


def ledger_tail(n: int = 15):
    """Most recent n ledger entries, newest first, for display in the app."""
    _ensure_table()
    return read_sql(
        "SELECT ledger_id, ts, event_type, ref_id, record_hash "
        "FROM governance_ledger ORDER BY ledger_id DESC LIMIT :n", n=n)


if __name__ == "__main__":
    print(notarize("selftest", "cli", {"note": "manual run from core/notarization.py"}))
    print(verify_chain())
