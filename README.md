# SAR Transaction Monitoring System

A Python + MySQL simulation of an AML transaction-monitoring and Suspicious Activity Report (SAR) workflow, using synthetic financial data. The system flags suspicious transaction patterns, generates alerts, and organizes them into cases for analyst review; the final SAR decision remains with a human analyst.

**Status:** Schema, data ingestion, and the first detection rule (RULE-001-VELOCITY) complete. Alert persistence, case management, and the analyst UI are in progress.

## Architecture

- Python 3, MySQL (developed against XAMPP)
- DB access via raw SQL / `pymysql`
- Data source: PaySim (Kaggle synthetic transactions dataset)
- First detection typology implemented: velocity/volume spikes (RULE-001-VELOCITY)
- Analyst interface: Flask/Streamlit (planned)

## Project structure

```
SAR_project/
├── create_schema.py          # one-time setup: creates the database + transactions table
├── sar_main.py               # entry point: loads a transaction sample into the database
├── classes/
│   └── db_connect.py         # DB_Connect — a small pymysql wrapper class
├── functions/
│   ├── load_functions.py     # CSV-to-database loading logic
│   └── detection_functions.py # RULE-001-VELOCITY detection logic
├── test_cases/               # unit tests for detection logic
├── text_files/
│   └── paysim.csv            # source dataset (gitignored — see .gitignore)
├── docs/                     # Pydoc-generated documentation (planned)
└── notes/                    # session notes including a running "lessons learned" log
```

## Setup

1. Install and start MySQL (developed against XAMPP's bundled MySQL/MariaDB).
2. Download [PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1) and place it at `text_files/paysim.csv`.
3. Run the one-time schema setup:
       `python3 create_schema.py`
4. Load a sample of transactions:
       `python3 sar_main.py`

## Key design decisions

- `DECIMAL`, not `FLOAT`, for money columns
- Parameterized queries (`%s` placeholders), not string concatenation
- No `IF NOT EXISTS` on the schema's `CREATE TABLE`
- Raw SQL, not an ORM

## Roadmap

- [x] Database schema and transactions table
- [x] CSV data ingestion pipeline (5,000-row sample)
- [x] Velocity/volume-spike detection logic (RULE-001-VELOCITY)
- [ ] Alert generation and case grouping
- [ ] Flask/Streamlit analyst review UI
- [ ] Full dataset ingestion (currently a 5,000-row sample)
- [x] Test coverage for detection logic

## Session 4 — Alert persistence

- Added an `alerts` table with status, timestamps, rule/version information,
  the matched account, and supporting rule evidence.
- Added database-enforced duplicate prevention for retries of the same logical
  detection run.
- Added `run_detection.py` to execute RULE-001-VELOCITY and persist its results.
- Stored matching transaction IDs as JSON so the evidence remains structured.
- Added a real MySQL integration test covering persistence, database defaults,
  evidence, timestamps, duplicate prevention, and cleanup.
- Full automated test suite: 10 tests passing.

## Session 5 — Case and analyst workflow

- Added `cases`, `case_alerts`, and `case_notes` for grouping related alerts
  and preserving analyst review history.
- Added OPEN, IN_REVIEW, and CLOSED case statuses with named analyst notes,
  timestamps, and SAR_FILED or NO_SAR dispositions.
- Made case creation, alert linking, and the CASED alert status transactional
  so failed grouping attempts do not leave partial workflow data.
- Prevented duplicate alert links, notes after case closure, and changes to a
  recorded disposition.
- Kept the final SAR decision human-controlled rather than assigning it through
  detection logic.
- Full automated test suite: 24 tests passing.
