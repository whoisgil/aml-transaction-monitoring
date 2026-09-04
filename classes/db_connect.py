import pymysql

class DB_Connect():
    """A simple class for connecting to a database and performing queries"""

    def __init__(self, passed_db_username, passed_db_password, passed_database):
        """Initialize the connection settings used to reach the database"""
        self.passed_db_username = passed_db_username
        self.passed_db_password = passed_db_password
        self.passed_database = passed_database
        self.conn = None

    def __connect(self):
        """Creates the connection to the database when it is first needed"""

        # using 127.0.0.1 instead of localhost so pymysql connects over TCP,
        # since that is how XAMPP's MySQL is reached rather than a unix socket
        self.conn = pymysql.connect(host='127.0.0.1',
                        port=3306,
                        user=self.passed_db_username,
                        password=self.passed_db_password,
                        db=self.passed_database,
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor)

    def executeQuery(self, passed_query, passed_values=None):
        """Executes a database query for Inserts, Updates, and Deletes"""

        if not self.conn:
            self.__connect()

        # passed_values stays optional so this also covers plain DDL statements
        # that take no parameters, like CREATE TABLE
        with self.conn.cursor() as cursor:
            cursor.execute(passed_query, passed_values)

    def executeManyQuery(self, passed_query, passed_values):
        """Executes the same Insert query once for every row in a batch"""

        if not self.conn:
            self.__connect()

        with self.conn.cursor() as cursor:
            cursor.executemany(passed_query, passed_values)

    def executeSelectQuery(self, passed_query, passed_values=None):
        """Executes a SELECT database query and returns the results as a tuple-like structure"""

        if not self.conn:
            self.__connect()

        with self.conn.cursor() as cursor:
            cursor.execute(passed_query, passed_values)

        return cursor.fetchall()

    def close_connection(self):
        """Closes the database connection"""

        self.conn.close()
