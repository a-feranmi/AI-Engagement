# BredgePulse — Data Governance (Module 7)

Most portfolio projects at this stage stop at a dashboard and an app. This
project also implements the four Module 7 topics directly, not just as
slide-ware but as running code:

| Module 7 topic | Where it lives | What it actually does |
|---|---|---|
| **Ethics, IP & Data Protection** | `app/app.py` (role-based login), `data/` | Synthetic data only, no confidential client records; role-based access separates Administrator, Account Manager and read-only Guest views. An Account Manager sees only their own clients. |
| **Data Quality** | `etl/data_quality.py`, `core/data_quality_scorecard.py` | 41 rule-based checks mirroring the schema's CHECK and FOREIGN KEY constraints: ranges, allowed values, date logic, cross-field consistency (e.g. BEHS equals its weighted components, utilisation equals actual/expected hours), referential integrity, and uniqueness on each table's grain. Rolled up into four graded dimensions (completeness, validity, uniqueness, freshness) and shown live, with per-rule results, in the app's *Model & governance* tab. |
| **Data Notarization (Blockchain)** | `core/notarization.py` | A SHA-256 hash-chain ledger. Every model run, intervention log and outcome closure is appended as a row whose hash depends on its own content **and** the hash of the row before it. Each model-run entry also carries SHA-256 digests of `all_predictions.csv`, `metrics.json`, the model file and the risk drivers, so every individual prediction is covered. `verify_chain()` recomputes the whole chain on demand and reports the exact row where history was altered, if any. |
| **Agile Scrum** | the 12-month roadmap (slides, Section 5) | Four quarterly **releases** (Q1 Foundation → Q2 Visibility → Q3 Intelligence → Q4 Optimisation), each delivered through two-week sprints with sprint reviews and retrospectives, and each closing with a release review against pilot KPIs. |

## Why a hash chain, not "real" blockchain

A public/distributed blockchain solves a problem BredgePulse doesn't have
trust between *mutually distrusting parties with no shared database*. Bredge
has one database and one accountable governance owner. What that owner
actually needs is **proof that no one, including an administrator quietly
edited a past prediction, intervention record or outcome.** A hash chain
gives that exact guarantee with zero new infrastructure: append-only writes,
each linked cryptographically to the one before it. This is the same
principle blockchains use (Bitcoin's block header includes the previous
block's hash); the difference is only whether you need many independent
validators to agree on it, which a single-organisation audit trail does not.

## How to verify it yourself

```python
from core.notarization import notarize, verify_chain, ledger_tail

notarize("intervention_logged", "ENG-00650", {"owner": "Account Manager"})
verify_chain()          # {"ok": True, "checked": N, "broken_at": None}
ledger_tail(10)         # most recent 10 ledger rows
```

Or in the app: **Model & governance → Decision notarization ledger → Verify
chain integrity.** Tampering with any past row (e.g. editing `payload` or
`record_hash` directly in the database) is detected immediately, the button
reports the exact `ledger_id` where the chain breaks.

## Limitations, stated openly

- This protects against **silent, undetected alteration**, not against a bad
  actor with full database access rewriting the whole chain from that point
  forward and re-hashing it consistently. A production system would also
  periodically export the latest `record_hash` to a write-once external
  store (an email digest, a signed log, or an actual anchoring transaction on
  a public chain) so even a full rewrite is detectable. That extension is a
  natural Phase 2, not implemented here.
- The Data Quality Scorecard's freshness dimension is a simple file-age proxy
  suitable for a synthetic dataset; a production version would check
  per-source ingestion SLAs instead.
- A file digest proves a prediction file has not changed since it was
  notarized; it does not by itself prove the file was produced correctly.
  That is what the model card, the tests and the reproducible build are for.
