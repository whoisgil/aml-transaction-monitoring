# importing needed libraries
import os

from classes.db_connect import DB_Connect
from functions.detection_functions import (
    fetchTransactionsForVelocityRule, detectVelocityRule, RULE_VERSION
)
from functions.alert_functions import persistAlerts
from functions.case_functions import groupAlertsIntoCases

# Database credentials come from the environment so no password lives in the code.
# Set them before running, e.g. export DB_PASSWORD='your-local-mysql-password'
db_username = os.environ.get("DB_USERNAME", "root")
db_password = os.environ.get("DB_PASSWORD")
db_name = os.environ.get("DB_NAME", "sar_project")


def main():
    """Runs Rule #1 against stored transactions and persists any resulting alerts"""

    if not db_password:
        raise SystemExit("Set the DB_PASSWORD environment variable before running.")

    sar_db = DB_Connect(db_username, db_password, db_name)

    transactions = fetchTransactionsForVelocityRule(sar_db)

    if not transactions:
        print("No transactions available for detection.")
        sar_db.close_connection()
        return

    as_of_step = max(row["step"] for row in transactions)
    results = detectVelocityRule(transactions, as_of_step)
    inserted_count = persistAlerts(sar_db, results, RULE_VERSION, as_of_step)

    if results and inserted_count == 0:
        print(f"Detection run at step {as_of_step} already persisted, skipping.")
    else:
        print(f"Persisted {inserted_count} alert(s) for step {as_of_step}.")

    # Grouping runs even when alerts already existed so an interrupted run can finish.
    linked_count = groupAlertsIntoCases(sar_db)
    print(f"Linked {linked_count} alert(s) to cases.")

    sar_db.close_connection()



# calling main only when this file is run directly so Pydoc can import it safely
if __name__ == "__main__":
    main()
