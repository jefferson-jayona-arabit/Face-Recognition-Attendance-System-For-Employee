import mysql.connector
from mysql.connector import Error


DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "abcd1234",
    "database": "facerecognition"
}


def get_connection():
    """Return a new MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"[DB ERROR] Failed to connect: {e}")
        return None


def test_connection():
    """Test the database connection and print the result."""
    conn = get_connection()
    if conn:
        print(f"[DB OK] Connected to '{DB_CONFIG['database']}' on port {DB_CONFIG['port']}")
        conn.close()
    else:
        print("[DB FAIL] Could not connect. Check your DB_CONFIG settings.")


if __name__ == "__main__":
    test_connection()