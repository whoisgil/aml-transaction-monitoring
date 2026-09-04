# SAR Transaction Monitoring System

A Python + MySQL simulation of an AML transaction-monitoring and Suspicious Activity Report (SAR) workflow, using synthetic financial data. The system flags suspicious transaction patterns, generates alerts, and organizes them into cases for analyst review; the final SAR decision remains with a human analyst.

**Status:** Schema and data ingestion pipeline complete. Detection logic and analyst UI in progress.

## Architecture

- Python 3, MySQL (developed against XAMPP)
- DB access via r
- Data source: PaySim (Kaggle synthetic transactions dataset)
- First detection spikes
- Analyst interface: Flask/Streamlit (planned)

## Project structure

    SAR_project/
    ├── create_sc setup: creates the database + transactions table
    ├── sar_main.point: loads atransaction sample into the database
    ├── classes/
    │   └── db_connect.py          # DB_Connect — a small pymysql wrapper c
    ├── functions/
    │   └── load_-database loadinglogic
    ├── test_caseests (planned)
    ├── text_files/
    │   └── paysie dataset(gitignored)
    ├── docs/    -generateddocumentation (planned)
    └── notes/   on notes andlessons-learned log

## Setup

1. Install and start MySQL (developed against XAMPP's bundled
MySQL/MariaDB).
2. Download
[PaySim](https://laxi/paysim1) andplace it at `text_files/paysim.csv`.
3. Run the one-ti
       python3 create_schema.py
4. Load a sample
       python3 sar_main.py

## Key design decisions

- `DECIMAL`, not `FLOAT`, for money columns
- Parameterized q, not stringconcatenation
- No `IF NOT EXISE TABLE`
- Raw SQL, not an ORM

## Roadmap
- [x] Database schema and transactions table
- [x] CSV data ingestion pipeline (5,000-row sample)
- [ ] Velocity/volume-spike detection logic
- [ ] Alert generation and case grouping
- [ ] Flask/Streamlit analyst review UI
- [ ] Full dataset ingestion (currently a 5,000-row sample)
- [ ] Test coverage for detection logic