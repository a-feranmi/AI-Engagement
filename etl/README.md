# ETL

Pipeline contract:

1. Extract synthetic CSV/JSON source files.
2. Validate schema and business rules.
3. Clean missing/duplicate/invalid values.
4. Transform to core entities.
5. Load PostgreSQL `core` tables.
6. Run data-quality checks.
7. Build analytics/features.

The next implementation task is to add `extract.py`, `transform.py`, `validate.py`, and `load.py` against the synthetic source files.
