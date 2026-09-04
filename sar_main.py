# main program for the SAR transaction-monitoring project

# importing needed libraries
from classes.db_connect import DB_Connect
from functions.load_functions import loadSampleTransactions

# setting the database credentials and file locations used by this script
db_username = "root"
db_password = ""
db_name = "sar_project"
csv_path = "text_files/paysim.csv"
sample_size = 5000


def main():
    """Connects to the database and loads a sample of transactions from the CSV"""

    sar_db = DB_Connect(db_username, db_password, db_name)

    inserted_count = loadSampleTransactions(sar_db, csv_path, sample_size)

    print("Inserted " + str(inserted_count) + " rows into the transactions table.")

    sar_db.close_connection()


# calling main only when this file is run directly so Pydoc can import it safely
if __name__ == "__main__":
    main()
