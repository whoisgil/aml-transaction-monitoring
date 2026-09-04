# Functions that load transaction data from a CSV file into the database

# importing needed libraries
import csv
import itertools


def loadSampleTransactions(passed_db, passed_csv_path, passed_sample_size):
    """Reads a sample of rows from the transactions CSV and inserts them into the database"""

    rows_to_insert = []

    # reading only the first N rows so today's sample stays small and fast
    with open(passed_csv_path, newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in itertools.islice(reader, passed_sample_size):
            rows_to_insert.append((
                int(row["step"]),
                row["type"],
                float(row["amount"]),
                row["nameOrig"],
                float(row["oldbalanceOrg"]),
                float(row["newbalanceOrig"]),
                row["nameDest"],
                float(row["oldbalanceDest"]),
                float(row["newbalanceDest"]),
                int(row["isFraud"]),
                int(row["isFlaggedFraud"]),
            ))

    # building the parameterized insert statement, one placeholder per column
    insert_sql = """
        INSERT INTO transactions
            (step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig,
             nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    passed_db.executeManyQuery(insert_sql, rows_to_insert)
    passed_db.conn.commit()

    return len(rows_to_insert)
