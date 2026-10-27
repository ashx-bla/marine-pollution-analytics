from multiprocessing import connection
import os
import mysql.connector

import os
import mysql.connector


def get_db_connection():
    connection = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get(
            "DB_NAME",
            "marine_pollution_db"
        )
    )

    # Set MySQL session timezone to IST
    cursor = connection.cursor()
    cursor.execute("SET time_zone = '+05:30'")
    cursor.close()

    return connection