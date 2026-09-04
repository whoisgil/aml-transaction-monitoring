# One-time setup script that creates the sar_project database and the transactions table

# importing needed libraries
import pymysql


def main():
    """Creates the sar_project database and transactions table if they do not already exist"""

    # connecting without a database selected since sar_project may not exist yet
    connection = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='',
    )

    cursor = connection.cursor()

    # creating the database, then switching the session to it
    cursor.execute("CREATE DATABASE IF NOT EXISTS sar_project")
    cursor.execute("USE sar_project")

    # defining the transactions table schema
    cursor.execute("""CREATE TABLE transactions (
        id                INT     AUTO_INCREMENT PRIMARY KEY,
        step              INT,
        type              VARCHAR(20),
        amount            DECIMAL(18,2),
        nameOrig          VARCHAR(20),
        oldbalanceOrg     DECIMAL(18,2),
        newbalanceOrig    DECIMAL(18,2),
        nameDest          VARCHAR(20),
        oldbalanceDest    DECIMAL(18,2),
        newbalanceDest    DECIMAL(18,2),
        isFraud           TINYINT(1),
        isFlaggedFraud    TINYINT(1)
    );
    """)

    # saving the schema and closing the connection cleanly
    connection.commit()
    cursor.close()
    connection.close()


# calling main only when this file is run directly so Pydoc can import it safely
if __name__ == "__main__":
    main()
