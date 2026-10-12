from db import get_db_connection

try:
    con = get_db_connection()

    if con.is_connected():
        print("MySQL connected successfully!")

    con.close()

except Exception as e:
    print("Connection failed:", e)