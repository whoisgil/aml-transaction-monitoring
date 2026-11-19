# main program for the SAR transaction-monitoring project

# importing needed libraries
import os

from classes.db_connect import DB_Connect
from functions.load_functions import loadSampleTransactions

# Database credentials come from the environment so no password lives in the code.
# Set them before running, e.g. export DB_PASSWORD='your-local-mysql-password'
db_username = os.environ.get("DB_USERNAME", "root")
db_password = os.environ.get("DB_PASSWORD")
db_name = os.environ.get("DB_NAME", "sar_project")
csv_path = "text_files/paysim.csv"
sample_size = 5000


def main():
    """Connects to the database and loads a sample of transactions from the CSV"""

    if not db_password:
        raise SystemExit("Set the DB_PASSWORD environment variable before running.")

    sar_db = DB_Connect(db_username, db_password, db_name)

    existing_rows = sar_db.executeSelectQuery("SELECT COUNT(*) AS count FROM transactions")

    existing_count = existing_rows[0]["count"]

    if existing_count > 0:
        print(
        f"Transactions table already contains {existing_count} rows. "
        "Loading again would create duplicate data.")

        sar_db.close_connection()
        return

    inserted_count = loadSampleTransactions(sar_db, csv_path, sample_size)

    row_count = sar_db.executeSelectQuery("select COUNT(*) AS count FROM transactions")

    database_count = row_count[0]["count"]

    if database_count == inserted_count:
        print(f"Validation passed: {database_count} transactions loaded")
    else:
        print(f"Warning: expected {inserted_count} rows, "
              f"but the database contains {database_count}")

    sar_db.close_connection()

    print("Inserted " + str(inserted_count) + " rows into the transactions table.")


# calling main only when this file is run directly so Pydoc can import it safely
if __name__ == "__main__":
    main()
