# importing needed libraries

from classes.db_connect import DB_Connect
from functions.detection_functions import (
    fetchTransactionsForVelocityRule, detectVelocityRule, RULE_VERSION
)
from functions.alert_functions import persistAlerts


db_username = "root"
db_password = ""
db_name = "sar_project"


def main():
    """Runs Rule #1 against stored transactions and persists any resulting alerts"""

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

    sar_db.close_connection()


# calling main only when this file is run directly so Pydoc can import it safely
if __name__ == "__main__":
    main()