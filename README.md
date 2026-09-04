# SAR Transaction Monitoring System

A Python + MySQL simulation of an AML transaction-monitoring and Suspicious Activity Report (SAR) workflow, using synthetic financial data. The system flags suspicious transaction patterns, generates alerts, and organizes them into cases for analyst review; the final SAR decision remains with a human analyst.

**Status:** Schema and data ingestion pipeline complete. Detection logic and analyst UI in progress.

## Architecture

- Python 3, MySQL (developed against XAMPP)
- DB access via raw SQL / `pymysql`
- Data source: PaySim (Kaggle synthetic transactions dataset)
- First detection typology: velocity/volume spikes
- Analyst interface: Flask/Streamlit (planned)

## Project structure

SAR_project/
    ├── create_schema.py         # one-time setup: creates the database + transactions table
    ├── sar_main.py                # entry point: loads a transaction sample into the database
    ├── classes/
    │   └── db_connect.py          # DB_Connect — a small pymysql wrapper class
    ├── functions/
    │   └── load_functions.py      # CSV-to-database loading logic
    ├── test_cases/                # unit tests (planned)
    ├── text_files/
    │   └── paysim.csv              # source dataset (gitignored — see .gitignore)
    ├── docs/                       # Pydoc-generated documentation (planned)
    └── notes/                      # session notes including a running "lessons learned" log

## Setup

1. Install and start MySQL (developed against XAMPP's bundled MySQL/MariaDB).
2. Download [PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1) and place it at `text_files/paysim.csv`.
3. Run the one-time schema setup:
       python3 create_schema.py
4. Load a sample of transactions:
       python3 sar_main.py

## Key design decisions

- `DECIMAL`, not `FLOAT`, for money columns
- Parameterized queries (`%s` placeholders), not string concatenation
- No `IF NOT EXISTS` on the schema's `CREATE TABLE`
- Raw SQL, not an ORM

## Roadmap

- [x] Database schema and transactions table
- [x] CSV data ingestion pipeline (5,000-row sample)
- [ ] Velocity/volume-spike detection logic
- [ ] Alert generation and case grouping
- [ ] Flask/Streamlit analyst review UI
- [ ] Full dataset ingestion (currently a 5,000-row sample)
- [ ] Test coverage for detection logic