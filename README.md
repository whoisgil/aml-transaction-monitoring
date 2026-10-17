# SAR Transaction Monitoring System

A Python + MySQL simulation of an AML transaction-monitoring and Suspicious Activity Report (SAR) workflow, using synthetic financial data. The system flags suspicious transaction patterns, generates alerts, and organizes them into cases for analyst review; the final SAR decision remains with a human analyst.

**Status:** Schema, sample ingestion, RULE-001-VELOCITY, alert persistence,
case management, and the Streamlit analyst interface are complete. Additional
detection rules and full-dataset scaling are planned.

## Architecture

- Python 3, MySQL (developed against XAMPP)
- DB access via raw SQL / `pymysql`
- Data source: PaySim (Kaggle synthetic transactions dataset)
- First detection typology implemented: velocity/volume spikes (RULE-001-VELOCITY)
- Analyst interface: Streamlit case-review application

## Project structure

```
SAR_project/
├── create_schema.py           # creates the database and workflow tables
├── sar_main.py                # loads a transaction sample into the database
├── run_detection.py           # runs detection, persists alerts, and groups cases
├── sar_app.py                 # Streamlit analyst investigation interface
├── requirements.txt           # pinned Python dependencies
├── classes/
│   └── db_connect.py          # small pymysql database wrapper
├── functions/
│   ├── alert_functions.py     # alert persistence
│   ├── case_functions.py      # case grouping and analyst workflow
│   ├── detection_functions.py # RULE-001-VELOCITY detection logic
│   ├── investigation_functions.py # case-review queries
│   └── load_functions.py      # CSV-to-database loading logic
├── test_cases/                # unit and MySQL integration tests
├── text_files/
│   └── paysim.csv             # source dataset (gitignored)
└── notes/                     # session notes and lessons learned
```

## Setup

1. Create and activate a Python virtual environment, then install dependencies:
       `pip install -r requirements.txt`
2. Install and start MySQL (developed against XAMPP's bundled MySQL/MariaDB).
3. Download [PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1) and place it at `text_files/paysim.csv`.
4. Run the one-time schema setup:
       `python3 create_schema.py`
5. Load a sample of transactions:
       `python3 sar_main.py`
6. Run detection and group resulting alerts into cases:
       `python3 run_detection.py`
7. Start the analyst interface:
       `streamlit run sar_app.py`

## Key design decisions

- `DECIMAL`, not `FLOAT`, for money columns
- Parameterized queries (`%s` placeholders), not string concatenation
- No `IF NOT EXISTS` on the schema's `CREATE TABLE`
- Raw SQL, not an ORM
- Human-controlled SAR dispositions with named analyst attribution
- Transactional alert grouping and case-status audit notes

## Roadmap

- [x] Database schema and transactions table
- [x] CSV data ingestion pipeline (5,000-row sample)
- [x] Velocity/volume-spike detection logic (RULE-001-VELOCITY)
- [x] Alert generation and case grouping
- [x] Streamlit analyst review UI
- [ ] Full dataset ingestion (currently a 5,000-row sample)
- [x] Test coverage for detection, alerts, cases, and investigation queries

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

## Session 6 — Investigation interface

- Chose Streamlit and added a case-first review queue with optional closed-case
  visibility.
- Added case detail views for grouped alerts, decoded rule evidence, involved
  accounts, evidence transactions, and analyst notes.
- Added analyst controls for moving cases into review, adding notes, and
  recording a confirmed SAR_FILED or NO_SAR disposition.
- Persisted named status-transition audit notes and kept the status change and
  audit note in one transaction.
- Updated detection runs to group open alerts into cases automatically and
  safely resume grouping after an interrupted run.
- Added investigation-query and workflow coverage; the automated suite now
  contains 34 tests.
