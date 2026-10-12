
from werkzeug.security import generate_password_hash
from db import get_db_connection

USERNAME = input("Enter admin username: ").strip()
PASSWORD = input("Create admin password: ")

if not USERNAME or not PASSWORD:
    print("Username and password cannot be empty.")
else:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT admin_id FROM admin_users WHERE username = %s",
            (USERNAME,)
        )

        if cursor.fetchone():
            print("This admin username already exists.")
        else:
            password_hash = generate_password_hash(PASSWORD)

            cursor.execute(
                """
                INSERT INTO admin_users (username, password_hash)
                VALUES (%s, %s)
                """,
                (USERNAME, password_hash)
            )

            conn.commit()
            print("Admin account created successfully!")

    except Exception as error:
        conn.rollback()
        print("Error creating admin account:", error)

    finally:
        cursor.close()
        conn.close()
